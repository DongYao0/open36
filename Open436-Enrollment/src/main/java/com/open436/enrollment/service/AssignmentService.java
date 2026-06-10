package com.open436.enrollment.service;

import com.open436.enrollment.dto.*;
import com.open436.enrollment.entity.Assignment;
import com.open436.enrollment.entity.AssignmentAllocation;
import com.open436.enrollment.entity.AssignmentSubmission;
import com.open436.enrollment.entity.EnrollmentApplication;
import com.open436.enrollment.repository.*;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageImpl;
import org.springframework.data.domain.PageRequest;
import org.springframework.http.*;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.client.RestTemplate;

import java.time.LocalDateTime;
import java.util.*;
import java.util.stream.Collectors;

@Slf4j
@Service
@RequiredArgsConstructor
public class AssignmentService {

    private final AssignmentRepository assignmentRepository;
    private final AssignmentAllocationRepository allocationRepository;
    private final AssignmentSubmissionRepository submissionRepository;
    private final EnrollmentRepository enrollmentRepository;
    private final RestTemplate restTemplate = new RestTemplate();

    @Value("${auth.service.url:http://localhost:8081}")
    private String authServiceUrl;

    // ==================== 作业 CRUD ====================

    @Transactional
    public AssignmentListResponse.AssignmentItem createAssignment(AssignmentRequest request, Long creatorId) {
        Assignment assignment = Assignment.builder()
                .title(request.getTitle())
                .description(request.getDescription())
                .deadline(request.getDeadline())
                .status("pending")
                .creatorId(creatorId)
                .build();
        assignment = assignmentRepository.save(assignment);
        log.info("作业创建: id={}, title={}", assignment.getId(), assignment.getTitle());
        return toAssignmentItem(assignment, 0L, 0L, 0L);
    }

    @Transactional(readOnly = true)
    public Page<AssignmentListResponse.AssignmentItem> list(String status, int page, int size) {
        Page<Assignment> assignmentPage;
        if (status != null && !status.isEmpty()) {
            assignmentPage = assignmentRepository.findByStatusOrderByCreatedAtDesc(status, PageRequest.of(page - 1, size));
        } else {
            assignmentPage = assignmentRepository.findAllByOrderByCreatedAtDesc(PageRequest.of(page - 1, size));
        }

        List<AssignmentListResponse.AssignmentItem> items = assignmentPage.getContent().stream()
                .map(a -> {
                    long assignedCount = allocationRepository.countByAssignmentId(a.getId());
                    long submittedCount = submissionRepository.countByAssignmentIdAndStatus(a.getId(), "submitted");
                    long totalCount = assignedCount;
                    return toAssignmentItem(a, assignedCount, submittedCount, totalCount);
                })
                .toList();

        return new PageImpl<>(items, PageRequest.of(page - 1, size), assignmentPage.getTotalElements());
    }

    @Transactional
    public void delete(Long id) {
        Assignment assignment = assignmentRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("作业不存在"));
        allocationRepository.deleteByAssignmentId(id);
        submissionRepository.findByAssignmentIdOrderBySubmittedAtDesc(id)
                .forEach(s -> submissionRepository.delete(s));
        assignmentRepository.delete(assignment);
        log.info("作业删除: id={}, title={}", id, assignment.getTitle());
    }

    // ==================== 统计 ====================

    @Transactional
    public Map<String, Object> statistics() {
        autoExpireAssignments();
        List<Assignment> all = assignmentRepository.findAll();
        long total = all.size();
        long active = all.stream().filter(a -> "active".equals(a.getStatus())).count();
        long ended = all.stream().filter(a -> "ended".equals(a.getStatus())).count();
        long pending = all.stream().filter(a -> "pending".equals(a.getStatus())).count();
        long collecting = active; // 进行中的作业即为待收集
        long collected = ended;
        int submitRate = total > 0 ? (int) Math.round((double) collected / total * 100) : 0;
        return Map.of(
                "total", total, "active", active, "ended", ended, "pending", pending,
                "collecting", collecting, "collected", collected, "submitRate", submitRate
        );
    }

    // ==================== 人员分配 ====================

    @Transactional(readOnly = true)
    public List<Map<String, Object>> getMembers(Long assignmentId, String keyword, String filter, String token) {
        List<AssignmentAllocation> allocations = allocationRepository.findByAssignmentIdOrderByAssignedAtDesc(assignmentId);
        Set<Long> allocatedStudentIds = allocations.stream()
                .map(AssignmentAllocation::getStudentId).collect(Collectors.toSet());
        Map<Long, AssignmentAllocation> allocMap = allocations.stream()
                .collect(Collectors.toMap(AssignmentAllocation::getStudentId, a -> a, (a, b) -> a));

        // 获取所有报名学生作为候选池
        List<EnrollmentApplication> apps = enrollmentRepository.findByStatus("approved");
        apps.addAll(enrollmentRepository.findByStatus("pending"));

        // 收集所有需要查询的用户ID（报名学生 + 已分配但不在报名中的学生）
        Set<Long> allUserIds = new HashSet<>(apps.stream().map(EnrollmentApplication::getAuthUserId).toList());
        allUserIds.addAll(allocatedStudentIds);
        Map<Long, Map<String, Object>> userMap = batchFetchUserInfo(new ArrayList<>(allUserIds), token);

        List<Map<String, Object>> result = new ArrayList<>();
        Set<Long> processedIds = new HashSet<>();

        // 1. 先添加报名学生（含分配状态）
        for (EnrollmentApplication app : apps) {
            Long uid = app.getAuthUserId();
            processedIds.add(uid);
            Map<String, Object> user = userMap.get(uid);
            boolean assigned = allocatedStudentIds.contains(uid);
            AssignmentAllocation alloc = allocMap.get(uid);

            Map<String, Object> item = new LinkedHashMap<>();
            item.put("studentId", uid);
            item.put("studentName", user != null ? user.getOrDefault("realName", user.get("username")) : alloc.getStudentName());
            item.put("studentNo", user != null ? user.get("studentId") : alloc.getStudentNo());
            item.put("major", user != null ? user.get("major") : alloc.getMajor());
            item.put("direction", alloc != null ? alloc.getDirection() : "");
            item.put("assigned", assigned);
            item.put("assignedAt", alloc != null ? alloc.getAssignedAt() : null);
            result.add(item);
        }

        // 2. 补充已分配但不在报名表中的学生
        for (AssignmentAllocation alloc : allocations) {
            if (processedIds.contains(alloc.getStudentId())) continue;
            Map<String, Object> user = userMap.get(alloc.getStudentId());
            Map<String, Object> item = new LinkedHashMap<>();
            item.put("studentId", alloc.getStudentId());
            item.put("studentName", user != null ? user.getOrDefault("realName", user.get("username")) : alloc.getStudentName());
            item.put("studentNo", user != null ? user.get("studentId") : alloc.getStudentNo());
            item.put("major", user != null ? user.get("major") : alloc.getMajor());
            item.put("direction", alloc.getDirection());
            item.put("assigned", true);
            item.put("assignedAt", alloc.getAssignedAt());
            result.add(item);
        }

        // 过滤
        if ("assigned".equals(filter)) {
            result = result.stream().filter(m -> (Boolean) m.get("assigned")).toList();
        } else if ("unassigned".equals(filter)) {
            result = result.stream().filter(m -> !(Boolean) m.get("assigned")).toList();
        }
        if (keyword != null && !keyword.isEmpty()) {
            String kw = keyword.toLowerCase();
            result = result.stream().filter(m ->
                String.valueOf(m.get("studentName")).toLowerCase().contains(kw) ||
                String.valueOf(m.get("studentNo")).contains(kw)
            ).toList();
        }
        return result;
    }

    @Transactional
    public void allocate(Long assignmentId, List<Long> studentIds, String token) {
        assignmentRepository.findById(assignmentId)
                .orElseThrow(() -> new RuntimeException("作业不存在"));

        Map<Long, Map<String, Object>> userMap = batchFetchUserInfo(studentIds, token);

        for (Long studentId : studentIds) {
            if (allocationRepository.existsByAssignmentIdAndStudentId(assignmentId, studentId)) {
                continue; // 已分配，跳过
            }
            Map<String, Object> user = userMap.get(studentId);
            String studentName = user != null ? String.valueOf(user.getOrDefault("realName", user.get("username"))) : "";
            String studentNo = user != null ? String.valueOf(user.getOrDefault("studentId", "")) : "";
            String major = user != null ? String.valueOf(user.getOrDefault("major", "")) : "";

            AssignmentAllocation allocation = AssignmentAllocation.builder()
                    .assignmentId(assignmentId)
                    .studentId(studentId)
                    .studentName(studentName)
                    .studentNo(studentNo)
                    .major(major)
                    .direction("")
                    .build();
            allocationRepository.save(allocation);

            // 同时创建空的提交记录
            if (!submissionRepository.existsByAssignmentIdAndStudentId(assignmentId, studentId)) {
                AssignmentSubmission submission = AssignmentSubmission.builder()
                        .assignmentId(assignmentId)
                        .studentId(studentId)
                        .studentName(studentName)
                        .studentNo(studentNo)
                        .major(major)
                        .direction("")
                        .status("unsubmitted")
                        .build();
                submissionRepository.save(submission);
            }
        }
        // 自动激活作业状态
        activateIfNeeded(assignmentId);
        log.info("作业分配: assignmentId={}, count={}", assignmentId, studentIds.size());
    }

    @Transactional
    public void removeAllocation(Long assignmentId, Long studentId) {
        allocationRepository.deleteByAssignmentIdAndStudentId(assignmentId, studentId);
        submissionRepository.findByAssignmentIdAndStudentId(assignmentId, studentId)
                .ifPresent(s -> submissionRepository.delete(s));
        log.info("作业移除分配: assignmentId={}, studentId={}", assignmentId, studentId);
    }

    @Transactional
    public void batchRemoveAllocations(Long assignmentId, List<Long> studentIds) {
        for (Long studentId : studentIds) {
            removeAllocation(assignmentId, studentId);
        }
        log.info("批量移除分配: assignmentId={}, count={}", assignmentId, studentIds.size());
    }

    // ==================== 学生池 ====================

    @Transactional(readOnly = true)
    public List<Map<String, Object>> getStudentPool(Long assignmentId, String keyword, String token) {
        Set<Long> allocatedIds = new HashSet<>(allocationRepository.findStudentIdsByAssignmentId(assignmentId));

        List<EnrollmentApplication> apps = enrollmentRepository.findByStatus("approved");
        List<EnrollmentApplication> pendingApps = enrollmentRepository.findByStatus("pending");
        List<EnrollmentApplication> allApps = new ArrayList<>(apps);
        allApps.addAll(pendingApps);

        Map<Long, Map<String, Object>> userMap = batchFetchUserInfo(
                allApps.stream().map(EnrollmentApplication::getAuthUserId).toList(), token);

        List<Map<String, Object>> result = new ArrayList<>();
        for (EnrollmentApplication app : allApps) {
            if (allocatedIds.contains(app.getAuthUserId())) continue; // 已分配的不显示
            Map<String, Object> user = userMap.get(app.getAuthUserId());
            if (user == null) continue;

            Map<String, Object> item = new LinkedHashMap<>();
            item.put("studentId", app.getAuthUserId());
            item.put("studentName", user.getOrDefault("realName", user.get("username")));
            item.put("studentNo", user.get("studentId"));
            item.put("major", user.get("major"));
            item.put("direction", "");
            result.add(item);
        }

        if (keyword != null && !keyword.isEmpty()) {
            String kw = keyword.toLowerCase();
            result = result.stream().filter(m ->
                String.valueOf(m.get("studentName")).toLowerCase().contains(kw) ||
                String.valueOf(m.get("studentNo")).contains(kw)
            ).toList();
        }
        return result;
    }

    // ==================== 提交管理 ====================

    @Transactional(readOnly = true)
    public List<Map<String, Object>> getSubmissions(Long assignmentId, String keyword, String filter, String token) {
        List<AssignmentSubmission> submissions = submissionRepository.findByAssignmentIdOrderBySubmittedAtDesc(assignmentId);

        // 补充 Auth 用户信息
        List<Long> studentIds = submissions.stream().map(AssignmentSubmission::getStudentId).toList();
        Map<Long, Map<String, Object>> userMap = batchFetchUserInfo(studentIds, token);

        List<Map<String, Object>> result = new ArrayList<>();
        for (AssignmentSubmission s : submissions) {
            Map<String, Object> user = userMap.get(s.getStudentId());
            Map<String, Object> item = new LinkedHashMap<>();
            item.put("id", s.getId());
            item.put("studentId", s.getStudentId());
            item.put("studentName", s.getStudentName());
            item.put("studentNo", s.getStudentNo());
            item.put("major", s.getMajor());
            item.put("direction", s.getDirection());
            item.put("status", s.getStatus());
            item.put("submittedAt", s.getSubmittedAt());
            item.put("content", s.getContent());
            // 解析文件路径
            item.put("files", parseFiles(s.getFilePaths()));
            if (user != null) {
                item.put("phone", user.get("phone"));
            }
            result.add(item);
        }

        if ("submitted".equals(filter)) {
            result = result.stream().filter(m -> "submitted".equals(m.get("status"))).toList();
        } else if ("unsubmitted".equals(filter)) {
            result = result.stream().filter(m -> "unsubmitted".equals(m.get("status"))).toList();
        }
        if (keyword != null && !keyword.isEmpty()) {
            String kw = keyword.toLowerCase();
            result = result.stream().filter(m ->
                String.valueOf(m.get("studentName")).toLowerCase().contains(kw) ||
                String.valueOf(m.get("studentNo")).contains(kw)
            ).toList();
        }
        return result;
    }

    @Transactional(readOnly = true)
    public Map<String, Object> getSubmissionDetail(Long submissionId, String token) {
        AssignmentSubmission s = submissionRepository.findById(submissionId)
                .orElseThrow(() -> new RuntimeException("提交记录不存在"));
        Map<String, Object> user = fetchSingleUserInfo(s.getStudentId(), token);

        Map<String, Object> result = new LinkedHashMap<>();
        result.put("id", s.getId());
        result.put("assignmentId", s.getAssignmentId());
        result.put("studentId", s.getStudentId());
        result.put("studentName", s.getStudentName());
        result.put("studentNo", s.getStudentNo());
        result.put("major", s.getMajor());
        result.put("direction", s.getDirection());
        result.put("status", s.getStatus());
        result.put("content", s.getContent());
        result.put("files", parseFiles(s.getFilePaths()));
        result.put("submittedAt", s.getSubmittedAt());
        result.put("codeContent", s.getContent()); // 代码内容复用 content 字段
        if (user != null) {
            result.put("phone", user.get("phone"));
        }
        return result;
    }

    @Transactional
    public void sendReminder(Long submissionId) {
        AssignmentSubmission s = submissionRepository.findById(submissionId)
                .orElseThrow(() -> new RuntimeException("提交记录不存在"));
        // TODO: 集成消息通知服务，目前仅记录日志
        log.info("催交通知: assignmentId={}, studentId={}, studentName={}",
                s.getAssignmentId(), s.getStudentId(), s.getStudentName());
    }

    // ==================== 工具方法 ====================

    private void autoExpireAssignments() {
        List<Assignment> expired = assignmentRepository.findExpiredActiveAssignments(LocalDateTime.now());
        for (Assignment a : expired) {
            a.setStatus("ended");
            assignmentRepository.save(a);
            log.info("作业自动截止: id={}, title={}", a.getId(), a.getTitle());
        }
    }

    private void activateIfNeeded(Long assignmentId) {
        Assignment a = assignmentRepository.findById(assignmentId).orElse(null);
        if (a != null && "pending".equals(a.getStatus())) {
            a.setStatus("active");
            assignmentRepository.save(a);
        }
    }

    private AssignmentListResponse.AssignmentItem toAssignmentItem(
            Assignment a, long assignedCount, long submittedCount, long totalCount) {
        return AssignmentListResponse.AssignmentItem.builder()
                .id(a.getId())
                .title(a.getTitle())
                .description(a.getDescription())
                .deadline(a.getDeadline())
                .status(a.getStatus())
                .assignedCount(assignedCount)
                .submittedCount(submittedCount)
                .totalCount(totalCount)
                .createdAt(a.getCreatedAt())
                .build();
    }

    private List<Map<String, String>> parseFiles(String filePaths) {
        List<Map<String, String>> files = new ArrayList<>();
        if (filePaths == null || filePaths.isBlank()) return files;
        try {
            com.fasterxml.jackson.databind.ObjectMapper mapper = new com.fasterxml.jackson.databind.ObjectMapper();
            List<Map<String, String>> parsed = mapper.readValue(filePaths,
                    new com.fasterxml.jackson.core.type.TypeReference<>() {});
            files = parsed;
        } catch (Exception e) {
            log.warn("解析文件路径JSON失败: {}", filePaths);
        }
        return files;
    }

    @SuppressWarnings("unchecked")
    private Map<Long, Map<String, Object>> batchFetchUserInfo(List<Long> authUserIds, String token) {
        Map<Long, Map<String, Object>> result = new HashMap<>();
        if (authUserIds == null || authUserIds.isEmpty()) return result;
        try {
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            if (token != null && !token.isEmpty()) headers.set("token", token);
            HttpEntity<List<Long>> entity = new HttpEntity<>(authUserIds, headers);
            ResponseEntity<Map> response = restTemplate.exchange(
                    authServiceUrl + "/api/auth/users/batch-info", HttpMethod.POST, entity, Map.class);
            if (response.getStatusCode().is2xxSuccessful() && response.getBody() != null) {
                Object data = response.getBody().get("data");
                if (data instanceof List) {
                    for (Object item : (List<?>) data) {
                        if (item instanceof Map) {
                            Map<String, Object> user = (Map<String, Object>) item;
                            Object id = user.get("id");
                            if (id != null) result.put(((Number) id).longValue(), user);
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
            headers.setContentType(MediaType.APPLICATION_JSON);
            if (token != null && !token.isEmpty()) headers.set("token", token);
            HttpEntity<Void> entity = new HttpEntity<>(headers);
            ResponseEntity<Map> response = restTemplate.exchange(
                    authServiceUrl + "/api/auth/users/" + authUserId, HttpMethod.GET, entity, Map.class);
            if (response.getStatusCode().is2xxSuccessful() && response.getBody() != null) {
                Object data = response.getBody().get("data");
                if (data instanceof Map) return (Map<String, Object>) data;
            }
        } catch (Exception e) {
            log.error("查询Auth用户信息失败: authUserId={}, error={}", authUserId, e.getMessage());
        }
        return null;
    }
}
