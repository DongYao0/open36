package com.open436.enrollment.service;

import com.open436.enrollment.dto.InterviewListResponse;
import com.open436.enrollment.dto.InterviewListResponse.InterviewRoundItem;
import com.open436.enrollment.dto.InterviewRecordRequest;
import com.open436.enrollment.dto.InterviewStatisticsResponse;
import com.open436.enrollment.entity.EnrollmentApplication;
import com.open436.enrollment.entity.Interview;
import com.open436.enrollment.repository.EnrollmentRepository;
import com.open436.enrollment.repository.InterviewRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageImpl;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Sort;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.client.RestTemplate;

import java.time.LocalDateTime;
import java.util.*;
import java.util.stream.Collectors;

@Slf4j
@Service
@RequiredArgsConstructor
public class InterviewService {

    private final InterviewRepository interviewRepository;
    private final EnrollmentRepository enrollmentRepository;
    private final RestTemplate restTemplate = new RestTemplate();

    @Value("${auth.service.url:http://localhost:8081}")
    private String authServiceUrl;

    /**
     * 获取待面试列表：从 enrollment_applications (status=pending) 中筛选
     * 关联面试记录，展示面试状态
     */
    @Transactional(readOnly = true)
    public Page<InterviewListResponse> list(String status, String keyword, int page, int size, String token) {
        // 1. 获取所有待审核的报名申请
        List<EnrollmentApplication> pendingApps = enrollmentRepository.findByStatus("pending");

        // 2. 查询所有相关面试记录，按 enrollmentId 分组
        List<Long> enrollmentIds = pendingApps.stream()
                .map(EnrollmentApplication::getId).toList();
        Map<Long, List<Interview>> interviewMap = new HashMap<>();
        if (!enrollmentIds.isEmpty()) {
            List<Interview> allInterviews = interviewRepository.findAllById(
                    interviewRepository.findAll().stream()
                            .filter(i -> enrollmentIds.contains(i.getEnrollmentId()))
                            .map(Interview::getId).toList()
            );
            // 重新查询：通过 enrollmentId 批量获取
            for (Long eid : enrollmentIds) {
                interviewMap.put(eid, interviewRepository.findByEnrollmentIdOrderByRoundAsc(eid));
            }
        }

        // 3. 批量查询 Auth 用户信息
        Map<Long, Map<String, Object>> userMap = batchFetchUserInfo(
                pendingApps.stream().map(EnrollmentApplication::getAuthUserId).toList(), token
        );

        // 4. 组装响应
        List<InterviewListResponse> responses = pendingApps.stream()
                .map(app -> {
                    Map<String, Object> user = userMap.get(app.getAuthUserId());
                    List<Interview> interviews = interviewMap.getOrDefault(app.getId(), List.of());

                    // 确定面试状态
                    String interviewStatus = determineInterviewStatus(interviews, status);

                    return toListResponse(app, interviews, user, interviewStatus);
                })
                .filter(Objects::nonNull)
                .toList();

        // 5. 按 status 过滤
        List<InterviewListResponse> filtered = responses;
        if (status != null && !status.isEmpty()) {
            filtered = responses.stream()
                    .filter(r -> status.equals(r.getStatus()))
                    .toList();
        }

        // 6. 关键词过滤
        if (keyword != null && !keyword.isEmpty()) {
            String kw = keyword.toLowerCase();
            filtered = filtered.stream()
                    .filter(r -> matchesKeyword(r, kw))
                    .toList();
        }

        // 7. 内存分页
        int total = filtered.size();
        int start = Math.min((page - 1) * size, total);
        int end = Math.min(start + size, total);
        List<InterviewListResponse> pageContent = start < total
                ? filtered.subList(start, end) : List.of();

        return new PageImpl<>(pageContent,
                PageRequest.of(page - 1, size), total);
    }

    private String determineInterviewStatus(List<Interview> interviews, String filterStatus) {
        if (interviews.isEmpty()) {
            return "pending";
        }
        // 取最新一轮面试状态
        Interview latest = interviews.get(interviews.size() - 1);
        return latest.getStatus();
    }

    private boolean matchesKeyword(InterviewListResponse r, String kw) {
        return (r.getUsername() != null && r.getUsername().toLowerCase().contains(kw)) ||
               (r.getRealName() != null && r.getRealName().toLowerCase().contains(kw)) ||
               (r.getStudentId() != null && r.getStudentId().contains(kw)) ||
               (r.getMajor() != null && r.getMajor().toLowerCase().contains(kw));
    }

    /**
     * 记录面试结果
     */
    @Transactional
    public InterviewListResponse recordInterview(InterviewRecordRequest request, String adminName, String token) {
        EnrollmentApplication app = enrollmentRepository.findById(request.getEnrollmentId())
                .orElseThrow(() -> new RuntimeException("报名申请不存在"));

        // 确定 round：默认使用第1轮，已有记录则更新最新一轮
        List<Interview> existing = interviewRepository.findByEnrollmentIdOrderByRoundAsc(request.getEnrollmentId());
        int round;
        Optional<Interview> existingOpt;
        if (request.getRound() != null) {
            round = request.getRound();
            existingOpt = interviewRepository.findByEnrollmentIdAndRound(request.getEnrollmentId(), round);
        } else if (!existing.isEmpty()) {
            // 已有记录，更新最新一轮
            Interview latest = existing.get(existing.size() - 1);
            round = latest.getRound();
            existingOpt = Optional.of(latest);
        } else {
            // 无记录，创建第1轮
            round = 1;
            existingOpt = Optional.empty();
        }

        Interview interview;
        if (existingOpt.isPresent()) {
            interview = existingOpt.get();
        } else {
            interview = Interview.builder()
                    .enrollmentId(request.getEnrollmentId())
                    .authUserId(app.getAuthUserId())
                    .round(round)
                    .status("pending")
                    .build();
        }

        // 更新面试详情
        if (request.getInterviewDate() != null) {
            interview.setInterviewDate(request.getInterviewDate());
        } else {
            interview.setInterviewDate(LocalDateTime.now());
        }
        interview.setInterviewer(request.getInterviewer() != null ? request.getInterviewer() : adminName);
        interview.setScore(request.getScore());
        interview.setSummary(request.getSummary());
        interview.setStrengths(request.getStrengths());
        interview.setWeaknesses(request.getWeaknesses());
        interview.setDirection(request.getDirection());

        interviewRepository.save(interview);
        log.info("面试记录保存: enrollmentId={}, round={}, interviewer={}",
                request.getEnrollmentId(), round, interview.getInterviewer());

        // 查询用户信息并返回
        Map<String, Object> userInfo = fetchSingleUserInfo(app.getAuthUserId(), token);
        List<Interview> allRounds = interviewRepository.findByEnrollmentIdOrderByRoundAsc(request.getEnrollmentId());
        return toListResponse(app, allRounds, userInfo, interview.getStatus());
    }

    /**
     * 更新面试状态 (通过/不通过)
     */
    @Transactional
    public InterviewListResponse updateInterviewStatus(Long interviewId, String status, String adminName, String token) {
        Interview interview = interviewRepository.findById(interviewId)
                .orElseThrow(() -> new RuntimeException("面试记录不存在"));

        if (!Set.of("passed", "failed", "pending").contains(status)) {
            throw new RuntimeException("无效的面试状态");
        }

        interview.setStatus(status);
        interviewRepository.save(interview);
        log.info("面试状态更新: interviewId={}, status={}, operator={}", interviewId, status, adminName);

        EnrollmentApplication app = enrollmentRepository.findById(interview.getEnrollmentId())
                .orElseThrow(() -> new RuntimeException("报名申请不存在"));
        Map<String, Object> userInfo = fetchSingleUserInfo(app.getAuthUserId(), token);
        List<Interview> allRounds = interviewRepository.findByEnrollmentIdOrderByRoundAsc(interview.getEnrollmentId());
        String displayStatus = determineInterviewStatus(allRounds, null);
        return toListResponse(app, allRounds, userInfo, displayStatus);
    }

    /**
     * 获取面试详情（含所有轮次）
     */
    @Transactional(readOnly = true)
    public InterviewListResponse getDetail(Long enrollmentId, String token) {
        EnrollmentApplication app = enrollmentRepository.findById(enrollmentId)
                .orElseThrow(() -> new RuntimeException("报名申请不存在"));

        List<Interview> allRounds = interviewRepository.findByEnrollmentIdOrderByRoundAsc(enrollmentId);
        Map<String, Object> userInfo = fetchSingleUserInfo(app.getAuthUserId(), token);
        String displayStatus = determineInterviewStatus(allRounds, null);
        return toListResponse(app, allRounds, userInfo, displayStatus);
    }

    /**
     * 面试统计
     */
    @Transactional(readOnly = true)
    public InterviewStatisticsResponse statistics() {
        List<EnrollmentApplication> pendingApps = enrollmentRepository.findByStatus("pending");
        long total = pendingApps.size();

        // 统计有面试记录的候选人
        long interviewed = 0;
        long passed = 0;
        long failed = 0;
        long noInterview = 0;

        for (EnrollmentApplication app : pendingApps) {
            List<Interview> interviews = interviewRepository
                    .findByEnrollmentIdOrderByRoundAsc(app.getId());
            if (interviews.isEmpty()) {
                noInterview++;
            } else {
                interviewed++;
                String latestStatus = interviews.get(interviews.size() - 1).getStatus();
                if ("passed".equals(latestStatus)) passed++;
                else if ("failed".equals(latestStatus)) failed++;
            }
        }

        int passRate = (passed + failed) > 0
                ? (int) Math.round((double) passed / (passed + failed) * 100) : 0;

        return InterviewStatisticsResponse.builder()
                .total(total)
                .pending(noInterview)
                .passed(passed)
                .failed(failed)
                .passRate(passRate)
                .build();
    }

    // === 私有工具方法 ===

    @SuppressWarnings("unchecked")
    private Map<Long, Map<String, Object>> batchFetchUserInfo(List<Long> authUserIds, String token) {
        Map<Long, Map<String, Object>> result = new HashMap<>();
        if (authUserIds == null || authUserIds.isEmpty()) return result;

        try {
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(org.springframework.http.MediaType.APPLICATION_JSON);
            if (token != null && !token.isEmpty()) {
                headers.set("token", token);
            }
            HttpEntity<List<Long>> entity = new HttpEntity<>(authUserIds, headers);
            ResponseEntity<Map> response = restTemplate.exchange(
                    authServiceUrl + "/api/auth/users/batch-info",
                    HttpMethod.POST, entity, Map.class);

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
            log.error("批量查询Auth用户信息失败: count={}, error={}", authUserIds.size(), e.getMessage());
        }
        return result;
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
                    HttpMethod.GET, entity, Map.class);

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

    private InterviewListResponse toListResponse(
            EnrollmentApplication app,
            List<Interview> interviews,
            Map<String, Object> user,
            String displayStatus) {

        // 用户基本信息
        String username = null, realName = null, studentId = null,
                phone = null, major = null;
        if (user != null) {
            username = (String) user.get("username");
            realName = (String) user.get("realName");
            studentId = (String) user.get("studentId");
            phone = (String) user.get("phone");
            major = (String) user.get("major");
        }

        // 最新一轮面试信息
        Interview latest = interviews.isEmpty() ? null
                : interviews.get(interviews.size() - 1);

        // 所有轮次摘要
        List<InterviewRoundItem> roundItems = interviews.stream()
                .map(i -> InterviewRoundItem.builder()
                        .id(i.getId())
                        .round(i.getRound())
                        .status(i.getStatus())
                        .interviewDate(i.getInterviewDate())
                        .interviewer(i.getInterviewer())
                        .score(i.getScore())
                        .summary(i.getSummary())
                        .strengths(i.getStrengths())
                        .weaknesses(i.getWeaknesses())
                        .direction(i.getDirection())
                        .createdAt(i.getCreatedAt())
                        .build())
                .toList();

        return InterviewListResponse.builder()
                .id(latest != null ? latest.getId() : null)
                .enrollmentId(app.getId())
                .authUserId(app.getAuthUserId())
                .username(username)
                .realName(realName)
                .studentId(studentId)
                .phone(phone)
                .major(major)
                .selfIntro(app.getSelfIntro())
                .skills(app.getSkills())
                .status(displayStatus)
                .round(latest != null ? latest.getRound() : null)
                .interviewDate(latest != null ? latest.getInterviewDate() : null)
                .interviewer(latest != null ? latest.getInterviewer() : null)
                .score(latest != null ? latest.getScore() : null)
                .summary(latest != null ? latest.getSummary() : null)
                .strengths(latest != null ? latest.getStrengths() : null)
                .weaknesses(latest != null ? latest.getWeaknesses() : null)
                .direction(latest != null ? latest.getDirection() : null)
                .createdAt(latest != null ? latest.getCreatedAt() : null)
                .updatedAt(latest != null ? latest.getUpdatedAt() : null)
                .rounds(roundItems)
                .build();
    }
}
