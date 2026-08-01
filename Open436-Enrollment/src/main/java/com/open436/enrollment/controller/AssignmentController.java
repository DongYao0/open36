package com.open436.enrollment.controller;

import com.open436.enrollment.dto.*;
import com.open436.enrollment.service.AssignmentService;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.data.domain.Page;
import org.springframework.http.*;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.client.RestTemplate;

import java.util.List;
import java.util.Map;

@Slf4j
@RestController
@RequestMapping("/api/assignment")
@RequiredArgsConstructor
public class AssignmentController {

    private final AssignmentService assignmentService;
    private final RestTemplate restTemplate = new RestTemplate();

    @Value("${auth.service.url:http://localhost:8081}")
    private String authServiceUrl;

    private Long checkAdmin(HttpServletRequest request) {
        String token = request.getHeader("token");
        if (token == null || token.isEmpty()) throw new RuntimeException("未登录");
        HttpHeaders headers = new HttpHeaders();
        headers.set("token", token);
        HttpEntity<Void> entity = new HttpEntity<>(headers);
        try {
            ResponseEntity<Map> response = restTemplate.exchange(
                    authServiceUrl + "/api/auth/current", HttpMethod.GET, entity, Map.class);
            Map<String, Object> body = response.getBody();
            if (body == null || body.get("data") == null) throw new RuntimeException("鉴权失败");
            @SuppressWarnings("unchecked")
            Map<String, Object> data = (Map<String, Object>) body.get("data");
            if (!"admin".equals(data.get("role"))) throw new RuntimeException("无管理员权限");
            Object id = data.get("id");
            return id != null ? ((Number) id).longValue() : null;
        } catch (RuntimeException e) {
            throw e;
        } catch (Exception e) {
            throw new RuntimeException("鉴权失败: " + e.getMessage());
        }
    }

    /** 作业列表 */
    @GetMapping("/")
    public ResponseEntity<ApiResponse<Map<String, Object>>> list(
            @RequestParam(required = false) String status,
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "10") int size,
            HttpServletRequest request) {
        checkAdmin(request);
        Page<AssignmentListResponse.AssignmentItem> result = assignmentService.list(status, page, size);
        return ResponseEntity.ok(ApiResponse.success(Map.of(
                "list", result.getContent(), "total", result.getTotalElements()
        )));
    }

    /** 作业统计 */
    @GetMapping("/statistics")
    public ResponseEntity<ApiResponse<Map<String, Object>>> statistics(HttpServletRequest request) {
        checkAdmin(request);
        return ResponseEntity.ok(ApiResponse.success(assignmentService.statistics()));
    }

    /** 创建作业 */
    @PostMapping("/")
    public ResponseEntity<ApiResponse<AssignmentListResponse.AssignmentItem>> create(
            @Valid @RequestBody AssignmentRequest req, HttpServletRequest request) {
        Long creatorId = checkAdmin(request);
        return ResponseEntity.ok(ApiResponse.success(assignmentService.createAssignment(req, creatorId)));
    }

    /** 删除作业 */
    @DeleteMapping("/{id}")
    public ResponseEntity<ApiResponse<Void>> delete(@PathVariable Long id, HttpServletRequest request) {
        checkAdmin(request);
        assignmentService.delete(id);
        return ResponseEntity.ok(ApiResponse.success());
    }

    /** 获取某作业的人员列表（含分配状态） */
    @GetMapping("/{id}/members")
    public ResponseEntity<ApiResponse<List<Map<String, Object>>>> members(
            @PathVariable Long id,
            @RequestParam(required = false) String keyword,
            @RequestParam(required = false) String filter,
            HttpServletRequest request) {
        checkAdmin(request);
        String token = request.getHeader("token");
        return ResponseEntity.ok(ApiResponse.success(assignmentService.getMembers(id, keyword, filter, token)));
    }

    /** 批量分配学生 */
    @PostMapping("/{id}/allocate")
    public ResponseEntity<ApiResponse<Void>> allocate(
            @PathVariable Long id, @Valid @RequestBody AllocationRequest req, HttpServletRequest request) {
        checkAdmin(request);
        String token = request.getHeader("token");
        assignmentService.allocate(id, req.getStudentIds(), token);
        return ResponseEntity.ok(ApiResponse.success());
    }

    /** 移除单个分配 */
    @DeleteMapping("/{id}/allocate/{studentId}")
    public ResponseEntity<ApiResponse<Void>> removeAllocation(
            @PathVariable Long id, @PathVariable Long studentId, HttpServletRequest request) {
        checkAdmin(request);
        assignmentService.removeAllocation(id, studentId);
        return ResponseEntity.ok(ApiResponse.success());
    }

    /** 批量移除分配 */
    @PostMapping("/{id}/allocate/batch-remove")
    public ResponseEntity<ApiResponse<Void>> batchRemove(
            @PathVariable Long id, @Valid @RequestBody AllocationRequest req, HttpServletRequest request) {
        checkAdmin(request);
        assignmentService.batchRemoveAllocations(id, req.getStudentIds());
        return ResponseEntity.ok(ApiResponse.success());
    }

    /** 可选学生池（未分配该作业的学生） */
    @GetMapping("/{id}/students")
    public ResponseEntity<ApiResponse<List<Map<String, Object>>>> studentPool(
            @PathVariable Long id,
            @RequestParam(required = false) String keyword,
            HttpServletRequest request) {
        checkAdmin(request);
        String token = request.getHeader("token");
        return ResponseEntity.ok(ApiResponse.success(assignmentService.getStudentPool(id, keyword, token)));
    }

    /** 某作业的提交列表 */
    @GetMapping("/{id}/submissions")
    public ResponseEntity<ApiResponse<List<Map<String, Object>>>> submissions(
            @PathVariable Long id,
            @RequestParam(required = false) String keyword,
            @RequestParam(required = false) String filter,
            HttpServletRequest request) {
        checkAdmin(request);
        String token = request.getHeader("token");
        return ResponseEntity.ok(ApiResponse.success(assignmentService.getSubmissions(id, keyword, filter, token)));
    }

    /** 单个提交详情 */
    @GetMapping("/submissions/{submissionId}")
    public ResponseEntity<ApiResponse<Map<String, Object>>> submissionDetail(
            @PathVariable Long submissionId, HttpServletRequest request) {
        checkAdmin(request);
        String token = request.getHeader("token");
        return ResponseEntity.ok(ApiResponse.success(assignmentService.getSubmissionDetail(submissionId, token)));
    }

    /** 发送催交通知 */
    @PostMapping("/submissions/{submissionId}/remind")
    public ResponseEntity<ApiResponse<Void>> sendReminder(
            @PathVariable Long submissionId, HttpServletRequest request) {
        checkAdmin(request);
        assignmentService.sendReminder(submissionId);
        return ResponseEntity.ok(ApiResponse.success());
    }

    /** 查询当前用户被分配的作业（客户端用） */
    @GetMapping("/my")
    public ResponseEntity<ApiResponse<List<Map<String, Object>>>> myAssignments(HttpServletRequest request) {
        Long userId = getCurrentUserId(request);
        List<Map<String, Object>> result = assignmentService.getMyAssignments(userId);
        return ResponseEntity.ok(ApiResponse.success(result));
    }

    /** 查询单个作业详情（客户端用） */
    @GetMapping("/my/{assignmentId}")
    public ResponseEntity<ApiResponse<Map<String, Object>>> myAssignmentDetail(
            @PathVariable Long assignmentId, HttpServletRequest request) {
        Long userId = getCurrentUserId(request);
        Map<String, Object> result = assignmentService.getMyAssignmentDetail(userId, assignmentId);
        return ResponseEntity.ok(ApiResponse.success(result));
    }

    /** 提交作业（客户端用） */
    @PostMapping("/my/{assignmentId}/submit")
    public ResponseEntity<ApiResponse<Void>> submitAssignment(
            @PathVariable Long assignmentId,
            @RequestBody Map<String, Object> body,
            HttpServletRequest request) {
        Long userId = getCurrentUserId(request);
        String content = (String) body.getOrDefault("content", "");
        @SuppressWarnings("unchecked")
        List<String> files = (List<String>) body.get("files");
        assignmentService.submitAssignment(userId, assignmentId, content, files);
        return ResponseEntity.ok(ApiResponse.success());
    }

    private Long getCurrentUserId(HttpServletRequest request) {
        String token = request.getHeader("token");
        if (token == null || token.isEmpty()) throw new RuntimeException("未登录");
        HttpHeaders headers = new HttpHeaders();
        headers.set("token", token);
        HttpEntity<Void> entity = new HttpEntity<>(headers);
        try {
            ResponseEntity<Map> response = restTemplate.exchange(
                    authServiceUrl + "/api/auth/current", HttpMethod.GET, entity, Map.class);
            Map<String, Object> body = response.getBody();
            if (body == null || body.get("data") == null) throw new RuntimeException("鉴权失败");
            @SuppressWarnings("unchecked")
            Map<String, Object> data = (Map<String, Object>) body.get("data");
            Object id = data.get("id");
            return id != null ? ((Number) id).longValue() : null;
        } catch (RuntimeException e) {
            throw e;
        } catch (Exception e) {
            throw new RuntimeException("鉴权失败: " + e.getMessage());
        }
    }
}
