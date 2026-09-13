package com.open436.enrollment.service;

import com.open436.enrollment.dto.*;
import com.open436.enrollment.entity.EnrollmentApplication;
import com.open436.enrollment.exception.EnrollConflictException;
import com.open436.enrollment.exception.EnrollRetryableException;
import com.open436.enrollment.repository.EnrollmentRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.client.HttpClientErrorException;
import org.springframework.web.client.HttpServerErrorException;
import org.springframework.web.client.ResourceAccessException;
import org.springframework.web.client.RestTemplate;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.HexFormat;
import java.util.List;
import java.util.Map;

/**
 * 报名服务（阶段5 幂等与一致性改造）
 *
 * 写入路径状态机（processing_status，与审核态 status 正交）：
 *
 *   RECEIVED → CREATING_USER → USER_CREATED → PENDING（成功）
 *        ↘ RETRYABLE_FAILED（网络超时；同 Key 重试可恢复）
 *        ↘ PERMANENT_FAILED（用户名真实冲突 / 幂等键内容漂移）
 *
 * 关键约束：
 *  - Auth 注册调用移出数据库事务：不再出现“远程请求占用 DB 连接”；
 *  - Auth 侧按同一 X-Idempotency-Key 幂等（超时重试不会重复建号）；
 *  - UNIQUE(idempotency_key) / UNIQUE(auth_user_id) 是并发最终防线，
 *    冲突统一转 409，绝不以 500 暴露数据库异常。
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class EnrollmentService {

    private final EnrollmentRepository enrollmentRepository;
    private final RestTemplate enrollmentRestTemplate;

    @Value("${auth.service.url:http://localhost:8081}")
    private String authServiceUrl;

    @Value("${internal.api-key:}")
    private String internalApiKey;

    /**
     * 报名提交（幂等）。controller 传入 X-Idempotency-Key；
     * 无 Key 的调用按用户名身份派生 Key，同样获得幂等保护。
     */
    public Long apply(ApplyRequest request, String idempotencyKeyHeader) {
        final String key = (idempotencyKeyHeader != null && !idempotencyKeyHeader.isBlank())
                ? idempotencyKeyHeader.trim()
                : "anon-" + sha256(request.getUsername().toLowerCase());
        final String fingerprint = fingerprint(request);

        EnrollmentApplication row = findOrInsertRow(key, fingerprint, request);
        row = runCreateUserPhase(row, request, key);
        row = finalizeEnrollment(row);
        log.info("报名提交成功: idemKey={}, authUserId={}", shortKey(key), row.getAuthUserId());
        return row.getId();
    }

    /** 兼容旧签名（无幂等头，等价于按用户名派生 Key） */
    public void apply(ApplyRequest request) {
        apply(request, null);
    }

    /**
     * 取已存在行或插入 RECEIVED 新行。
     * 同 Key 内容漂移 → 409；已成功 → 返回该行（调用方视为成功）；
     * PERMANENT_FAILED → 409 带原因；插入竞争 → 重读按已存在处理。
     */
    private EnrollmentApplication findOrInsertRow(String key, String fingerprint, ApplyRequest request) {
        EnrollmentApplication existing = enrollmentRepository.findByIdempotencyKey(key).orElse(null);
        if (existing == null) {
            EnrollmentApplication inserted = EnrollmentApplication.builder()
                    .idempotencyKey(key)
                    .requestFingerprint(fingerprint)
                    .processingStatus(EnrollmentApplication.PS_RECEIVED)
                    .selfIntro(request.getSelfIntro())
                    .skills(request.getSkills())
                    .status("pending")
                    .build();
            try {
                return enrollmentRepository.saveAndFlush(inserted);
            } catch (DataIntegrityViolationException race) {
                // 并发同 Key：唯一约束兜底，重读后按已存在处理
                existing = enrollmentRepository.findByIdempotencyKey(key).orElse(null);
                if (existing == null) {
                    throw new EnrollConflictException("请求重复提交，请刷新后查看报名结果");
                }
            }
        }
        if (!fingerprint.equals(existing.getRequestFingerprint())) {
            throw new EnrollConflictException("同一报名请求的内容已变化，请刷新页面重新提交");
        }
        if (EnrollmentApplication.PS_PERMANENT_FAILED.equals(existing.getProcessingStatus())) {
            throw new EnrollConflictException(
                    existing.getLastError() != null ? existing.getLastError() : "该报名无法完成，请联系管理员");
        }
        return existing; // RECEIVED/RETRYABLE_FAILED/CREATING_USER/USER_CREATED/PENDING 均继续推进
    }

    /**
     * 阶段2：Auth 建 pending 用户（无外层事务，快速失败）。
     * Auth 侧同 Key 幂等：超时重试拿到的是同一个用户。
     */
    private EnrollmentApplication runCreateUserPhase(EnrollmentApplication row, ApplyRequest request, String key) {
        if (EnrollmentApplication.PS_USER_CREATED.equals(row.getProcessingStatus())
                || EnrollmentApplication.PS_PENDING.equals(row.getProcessingStatus())) {
            return row; // 已建号（含对账恢复后的行）
        }
        transition(row, EnrollmentApplication.PS_CREATING_USER, null);

        Map<String, Object> body = new java.util.HashMap<>();
        body.put("username", request.getUsername());
        body.put("password", request.getPassword());
        body.put("studentId", request.getStudentId());
        body.put("realName", request.getRealName());
        body.put("phone", request.getPhone());
        body.put("major", request.getMajor());

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        headers.set("X-Idempotency-Key", key);
        HttpEntity<Map<String, Object>> entity = new HttpEntity<>(body, headers);

        ResponseEntity<Map> response;
        try {
            response = enrollmentRestTemplate.exchange(
                    authServiceUrl + "/api/auth/register", HttpMethod.POST, entity, Map.class);
        } catch (ResourceAccessException e) {
            // 网络超时/不可达：Auth 可能已建号（响应丢失），同 Key 重试会取回同一用户
            log.warn("调用Auth注册超时/不可达: idemKey={}, error={}", shortKey(key), e.getMessage());
            transition(row, EnrollmentApplication.PS_RETRYABLE_FAILED, "网络波动，请稍后重试提交");
            throw new EnrollRetryableException("报名服务暂时不可用，请稍后重试（不会重复创建账号）");
        } catch (HttpServerErrorException e) {
            log.error("Auth注册服务端错误: idemKey={}, status={}", shortKey(key), e.getStatusCode());
            transition(row, EnrollmentApplication.PS_RETRYABLE_FAILED, "注册服务暂时不可用，请稍后重试");
            throw new EnrollRetryableException("报名服务暂时不可用，请稍后重试");
        } catch (HttpClientErrorException e) {
            // 409：幂等键内容漂移 / 用户名真实冲突 / 处理中
            String remoteMsg = extractRemoteMessage(e);
            log.warn("Auth注册被拒绝: idemKey={}, status={}, msg={}",
                    shortKey(key), e.getStatusCode(), remoteMsg);
            transition(row, EnrollmentApplication.PS_PERMANENT_FAILED, remoteMsg);
            throw new EnrollConflictException(remoteMsg != null ? remoteMsg : "注册被拒绝");
        }

        Map<String, Object> data = response.getBody() != null
                ? (Map<String, Object>) response.getBody().get("data") : null;
        Number userId = data != null ? (Number) data.get("id") : null;
        if (userId == null) {
            transition(row, EnrollmentApplication.PS_RETRYABLE_FAILED, "注册响应异常，请重试");
            throw new EnrollRetryableException("报名服务响应异常，请稍后重试");
        }
        row.setAuthUserId(userId.longValue());
        transition(row, EnrollmentApplication.PS_USER_CREATED, null);
        return row;
    }

    /** 阶段3：落终态 PENDING；auth_user_id 唯一竞争 → 复位已有结果 */
    private EnrollmentApplication finalizeEnrollment(EnrollmentApplication row) {
        if (EnrollmentApplication.PS_PENDING.equals(row.getProcessingStatus())) {
            return row;
        }
        row.setProcessingStatus(EnrollmentApplication.PS_PENDING);
        row.setLastError(null);
        try {
            return enrollmentRepository.saveAndFlush(row);
        } catch (DataIntegrityViolationException race) {
            EnrollmentApplication winner = row.getAuthUserId() != null
                    ? enrollmentRepository.findByAuthUserId(row.getAuthUserId()).orElse(null) : null;
            if (winner != null) {
                return winner; // 同一用户的既有报名，幂等返回
            }
            throw new EnrollConflictException("请求重复提交，请刷新后查看报名结果");
        }
    }

    private void transition(EnrollmentApplication row, String status, String error) {
        row.setProcessingStatus(status);
        row.setLastError(error);
        enrollmentRepository.save(row);
    }

    /** 身份+报名内容指纹（不含密码；密码永不入日志/幂等表） */
    static String fingerprint(ApplyRequest request) {
        String material = String.join("|",
                nullSafe(request.getUsername()).toLowerCase(),
                nullSafe(request.getStudentId()),
                nullSafe(request.getRealName()),
                nullSafe(request.getPhone()),
                nullSafe(request.getMajor()),
                nullSafe(request.getSelfIntro()),
                nullSafe(request.getSkills()));
        return sha256(material);
    }

    private static String extractRemoteMessage(HttpClientErrorException e) {
        try {
            Map body = e.getResponseBodyAs(Map.class);
            Object msg = body != null ? body.get("message") : null;
            return msg != null ? msg.toString() : null;
        } catch (Exception ignore) {
            return null;
        }
    }

    private static String nullSafe(String value) {
        return value == null ? "" : value.trim();
    }

    private static String shortKey(String key) {
        return key.length() <= 8 ? "short" : key.substring(0, 8);
    }

    private static String sha256(String input) {
        try {
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            return HexFormat.of().formatHex(digest.digest(input.getBytes(StandardCharsets.UTF_8)));
        } catch (Exception e) {
            throw new IllegalStateException("SHA-256 unavailable", e);
        }
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
            ResponseEntity<String> response = enrollmentRestTemplate.exchange(
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
    public Page<ApplicationListResponse> list(String status, String keyword, String startDate, String endDate, int page, int size, String token) {
        // 1. 先按状态筛选（关键词过滤依赖 Auth 用户信息，需全量拉取后过滤）
        List<EnrollmentApplication> apps;
        if (status != null && !status.isEmpty()) {
            apps = enrollmentRepository.findByStatus(status);
        } else {
            apps = enrollmentRepository.findAll();
        }

        // 2. 按提交时间筛选 submittedAt
        LocalDate startD = parseDate(startDate);
        LocalDate endD = parseDate(endDate);
        if (startD != null || endD != null) {
            apps = apps.stream()
                    .filter(app -> inDateRange(app.getSubmittedAt(), startD, endD))
                    .toList();
        }

        // 3. 批量查询 Auth 服务获取用户详细信息
        Map<Long, Map<String, Object>> userMap = batchFetchUserInfo(apps, token);

        // 4. 组装响应并处理关键词过滤
        List<ApplicationListResponse> responses = apps.stream()
                .map(app -> toResponse(app, userMap.get(app.getAuthUserId())))
                .toList();

        if (keyword != null && !keyword.isEmpty()) {
            String kw = keyword.toLowerCase();
            responses = responses.stream()
                    .filter(r -> matchesKeyword(r, kw))
                    .toList();
        }

        // 5. 内存分页
        int total = responses.size();
        int start = Math.min((page - 1) * size, total);
        int end = Math.min(start + size, total);
        List<ApplicationListResponse> pageContent = start < total ? responses.subList(start, end) : List.of();

        return new org.springframework.data.domain.PageImpl<>(
                pageContent, PageRequest.of(page - 1, size, Sort.by(Sort.Direction.DESC, "submittedAt")), total);
    }

    private LocalDate parseDate(String dateStr) {
        if (dateStr == null || dateStr.isEmpty()) return null;
        try {
            return LocalDate.parse(dateStr, DateTimeFormatter.ofPattern("yyyy-MM-dd"));
        } catch (Exception e) {
            log.warn("解析日期失败: dateStr={}, error={}", dateStr, e.getMessage());
            return null;
        }
    }

    private boolean inDateRange(LocalDateTime dateTime, LocalDate startD, LocalDate endD) {
        if (dateTime == null) return false;
        LocalDate d = dateTime.toLocalDate();
        if (startD != null && d.isBefore(startD)) return false;
        if (endD != null && d.isAfter(endD)) return false;
        return true;
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
            ResponseEntity<Map> response = enrollmentRestTemplate.exchange(
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
            ResponseEntity<Map> response = enrollmentRestTemplate.exchange(
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
