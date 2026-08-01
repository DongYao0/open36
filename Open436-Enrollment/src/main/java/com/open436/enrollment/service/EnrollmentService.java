package com.open436.enrollment.service;

import com.open436.enrollment.dto.*;
import com.open436.enrollment.entity.EnrollmentApplication;
import com.open436.enrollment.repository.EnrollmentRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.client.RestTemplate;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;

@Slf4j
@Service
@RequiredArgsConstructor
public class EnrollmentService {

    private final EnrollmentRepository enrollmentRepository;
    private final RestTemplate restTemplate = new RestTemplate();

    @Value("${auth.service.url:http://localhost:8081}")
    private String authServiceUrl;

    @Transactional
    public void apply(ApplyRequest request) {
        // 1. 先在 Auth 服务创建 pending 用户（唯一可信用户数据源）
        Map<String, Object> body = new java.util.HashMap<>();
        body.put("username", request.getUsername());
        body.put("password", request.getPassword());
        body.put("studentId", request.getStudentId());
        body.put("realName", request.getRealName());
        body.put("phone", request.getPhone());
        body.put("major", request.getMajor());

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(org.springframework.http.MediaType.APPLICATION_JSON);
        HttpEntity<Map<String, Object>> entity = new HttpEntity<>(body, headers);

        ResponseEntity<Map> response;
        try {
            response = restTemplate.exchange(
                    authServiceUrl + "/api/auth/register",
                    HttpMethod.POST,
                    entity,
                    Map.class
            );
        } catch (Exception e) {
            log.error("调用Auth服务注册失败: username={}, error={}", request.getUsername(), e.getMessage());
            throw new RuntimeException("注册失败：" + e.getMessage());
        }

        if (!response.getStatusCode().is2xxSuccessful()) {
            throw new RuntimeException("创建用户失败: " + response.getStatusCode());
        }

        Map<String, Object> respBody = response.getBody();
        Map<String, Object> data = respBody != null ? (Map<String, Object>) respBody.get("data") : null;
        Integer userId = data != null ? (Integer) data.get("id") : null;
        if (userId == null) {
            throw new RuntimeException("创建用户后未返回用户ID");
        }
        Long authUserId = userId.longValue();

        // 2. 保存报名表（仅保留报名专属字段，用户信息以 Auth 为准）
        if (enrollmentRepository.existsByAuthUserId(authUserId)) {
            throw new RuntimeException("该用户已提交报名申请");
        }
        EnrollmentApplication app = EnrollmentApplication.builder()
                .authUserId(authUserId)
                .selfIntro(request.getSelfIntro())
                .skills(request.getSkills())
                .status("pending")
                .build();
        enrollmentRepository.save(app);
        log.info("报名提交成功: username={}, authUserId={}", request.getUsername(), authUserId);
    }

    @Transactional
    public ApplicationListResponse review(Long id, ReviewRequest request, String adminName, String token) {
        EnrollmentApplication app = enrollmentRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("申请不存在"));
        app.setStatus(request.getStatus());
        app.setReviewedAt(LocalDateTime.now());
        app.setReviewedBy(adminName);
        app.setReviewReason(request.getReason());
        enrollmentRepository.save(app);

        if ("approved".equals(request.getStatus()) && app.getAuthUserId() != null) {
            activateUserAndSyncHoj(app.getAuthUserId(), token);
        }
        log.info("审核完成: id={}, status={}, reviewer={}", id, request.getStatus(), adminName);

        // 查询 Auth 服务补充用户信息
        Map<String, Object> userInfo = fetchSingleUserInfo(app.getAuthUserId(), token);
        return toResponse(app, userInfo);
    }

    private void activateUserAndSyncHoj(Long authUserId, String token) {
        try {
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(org.springframework.http.MediaType.APPLICATION_JSON);
            if (token != null && !token.isEmpty()) {
                headers.set("token", token);
            }
            HttpEntity<Void> entity = new HttpEntity<>(headers);
            ResponseEntity<String> response = restTemplate.exchange(
                    authServiceUrl + "/api/auth/users/" + authUserId + "/activate-and-sync",
                    HttpMethod.POST,
                    entity,
                    String.class
            );
            if (response.getStatusCode().is2xxSuccessful()) {
                log.info("用户激活并同步HOJ成功: authUserId={}", authUserId);
            } else {
                log.warn("用户激活失败: authUserId={}, status={}", authUserId, response.getStatusCode());
            }
        } catch (Exception e) {
            log.error("调用Auth服务激活用户失败: authUserId={}, error={}", authUserId, e.getMessage());
            throw new RuntimeException("审核通过但激活用户失败: " + e.getMessage());
        }
    }

    @Transactional(readOnly = true)
    public Page<ApplicationListResponse> list(String status, String keyword, int page, int size, String token) {
        // 1. 先按状态筛选（关键词过滤依赖 Auth 用户信息，需全量拉取后过滤）
        List<EnrollmentApplication> apps;
        if (status != null && !status.isEmpty()) {
            apps = enrollmentRepository.findByStatus(status);
        } else {
            apps = enrollmentRepository.findAll();
        }

        // 2. 批量查询 Auth 服务获取用户详细信息
        Map<Long, Map<String, Object>> userMap = batchFetchUserInfo(apps, token);

        // 3. 组装响应并处理关键词过滤
        List<ApplicationListResponse> responses = apps.stream()
                .map(app -> toResponse(app, userMap.get(app.getAuthUserId())))
                .toList();

        if (keyword != null && !keyword.isEmpty()) {
            String kw = keyword.toLowerCase();
            responses = responses.stream()
                    .filter(r -> matchesKeyword(r, kw))
                    .toList();
        }

        // 4. 内存分页
        int total = responses.size();
        int start = Math.min((page - 1) * size, total);
        int end = Math.min(start + size, total);
        List<ApplicationListResponse> pageContent = start < total ? responses.subList(start, end) : List.of();

        return new org.springframework.data.domain.PageImpl<>(
                pageContent, PageRequest.of(page - 1, size, Sort.by(Sort.Direction.DESC, "submittedAt")), total);
    }

    private boolean matchesKeyword(ApplicationListResponse r, String kw) {
        return (r.getUsername() != null && r.getUsername().toLowerCase().contains(kw)) ||
               (r.getRealName() != null && r.getRealName().toLowerCase().contains(kw)) ||
               (r.getStudentId() != null && r.getStudentId().contains(kw)) ||
               (r.getMajor() != null && r.getMajor().toLowerCase().contains(kw));
    }

    /**
     * 批量从 Auth 服务查询用户信息
     */
    @SuppressWarnings("unchecked")
    private Map<Long, Map<String, Object>> batchFetchUserInfo(List<EnrollmentApplication> apps, String token) {
        Map<Long, Map<String, Object>> result = new java.util.HashMap<>();
        if (apps.isEmpty()) {
            return result;
        }
        List<Long> userIds = apps.stream().map(EnrollmentApplication::getAuthUserId).toList();
        try {
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(org.springframework.http.MediaType.APPLICATION_JSON);
            if (token != null && !token.isEmpty()) {
                headers.set("token", token);
            }
            HttpEntity<List<Long>> entity = new HttpEntity<>(userIds, headers);
            ResponseEntity<Map> response = restTemplate.exchange(
                    authServiceUrl + "/api/auth/users/batch-info",
                    HttpMethod.POST,
                    entity,
                    Map.class
            );
            if (response.getStatusCode().is2xxSuccessful() && response.getBody() != null) {
                Object data = response.getBody().get("data");
                if (data instanceof List) {
                    for (Object item : (List<?>) data) {
                        if (item instanceof Map) {
                            Map<String, Object> user = (Map<String, Object>) item;
                            Object id = user.get("id");
                            if (id != null) {
                                result.put(((Number) id).longValue(), user);
                            }
                        }
                    }
                }
            }
        } catch (Exception e) {
            log.error("批量查询Auth用户信息失败: count={}, error={}", userIds.size(), e.getMessage());
        }
        return result;
    }

    @Transactional(readOnly = true)
    public StatisticsResponse statistics() {
        long total = enrollmentRepository.count();
        long pending = enrollmentRepository.countByStatus("pending");
        long approved = enrollmentRepository.countByStatus("approved");
        long rejected = enrollmentRepository.countByStatus("rejected");
        int approvalRate = (approved + rejected) > 0 ? (int) Math.round((double) approved / (approved + rejected) * 100) : 0;
        return StatisticsResponse.builder()
                .total(total).pending(pending).approved(approved).rejected(rejected).approvalRate(approvalRate)
                .build();
    }

    @Transactional
    public void batchReview(BatchReviewRequest request, String adminName, String token) {
        for (Long id : request.getIds()) {
            ReviewRequest r = new ReviewRequest();
            r.setStatus(request.getStatus());
            r.setReason(request.getReason());
            review(id, r, adminName, token);
        }
    }

    @SuppressWarnings("unchecked")
    private Map<String, Object> fetchSingleUserInfo(Long authUserId, String token) {
        try {
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(org.springframework.http.MediaType.APPLICATION_JSON);
            if (token != null && !token.isEmpty()) {
                headers.set("token", token);
            }
            HttpEntity<Void> entity = new HttpEntity<>(headers);
            ResponseEntity<Map> response = restTemplate.exchange(
                    authServiceUrl + "/api/auth/users/" + authUserId,
                    HttpMethod.GET,
                    entity,
                    Map.class
            );
            if (response.getStatusCode().is2xxSuccessful() && response.getBody() != null) {
                Object data = response.getBody().get("data");
                if (data instanceof Map) {
                    return (Map<String, Object>) data;
                }
            }
        } catch (Exception e) {
            log.error("查询单个Auth用户信息失败: authUserId={}, error={}", authUserId, e.getMessage());
        }
        return null;
    }

    private ApplicationListResponse toResponse(EnrollmentApplication app, Map<String, Object> user) {
        String username = null;
        String realName = null;
        String studentId = null;
        String phone = null;
        String major = null;
        if (user != null) {
            username = (String) user.get("username");
            realName = (String) user.get("realName");
            studentId = (String) user.get("studentId");
            phone = (String) user.get("phone");
            major = (String) user.get("major");
        }
        return ApplicationListResponse.builder()
                .id(app.getId())
                .authUserId(app.getAuthUserId())
                .username(username)
                .realName(realName)
                .studentId(studentId)
                .phone(phone)
                .major(major)
                .selfIntro(app.getSelfIntro())
                .skills(app.getSkills())
                .status(app.getStatus())
                .submittedAt(app.getSubmittedAt())
                .reviewedAt(app.getReviewedAt())
                .reviewedBy(app.getReviewedBy())
                .reviewReason(app.getReviewReason())
                .build();
    }
}
