package com.open436.enrollment.controller;

import com.open436.enrollment.dto.ApiResponse;
import com.open436.enrollment.dto.BatchInterviewStatusRequest;
import com.open436.enrollment.dto.InterviewListResponse;
import com.open436.enrollment.dto.InterviewRecordRequest;
import com.open436.enrollment.dto.InterviewStatisticsResponse;
import com.open436.enrollment.service.InterviewService;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.data.domain.Page;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.client.RestTemplate;

import java.util.Map;

@Slf4j
@RestController
@RequestMapping("/api/interview")
@RequiredArgsConstructor
public class InterviewController {

    private final InterviewService interviewService;
    private final RestTemplate restTemplate = new RestTemplate();

    @Value("${auth.service.url:http://localhost:8081}")
    private String authServiceUrl;

    private void checkAdmin(HttpServletRequest request) {
        String token = request.getHeader("token");
        if (token == null || token.isEmpty()) {
            throw new RuntimeException("未登录");
        }
        HttpHeaders headers = new HttpHeaders();
        headers.set("token", token);
        HttpEntity<Void> entity = new HttpEntity<>(headers);
        try {
            ResponseEntity<Map> response = restTemplate.exchange(
                    authServiceUrl + "/api/auth/current",
                    HttpMethod.GET, entity, Map.class);
            Map<String, Object> body = response.getBody();
            if (body == null || body.get("data") == null) {
                throw new RuntimeException("鉴权失败");
            }
            @SuppressWarnings("unchecked")
            Map<String, Object> data = (Map<String, Object>) body.get("data");
            String role = (String) data.get("role");
            if (!"admin".equals(role)) {
                throw new RuntimeException("无管理员权限");
            }
        } catch (RuntimeException e) {
            throw e;
        } catch (Exception e) {
            throw new RuntimeException("鉴权失败: " + e.getMessage());
        }
    }

    /**
     * 获取面试列表（待审核报名人员 + 面试状态）
     */
    @GetMapping("/")
    public ResponseEntity<ApiResponse<Map<String, Object>>> list(
            @RequestParam(required = false) String status,
            @RequestParam(required = false) String keyword,
            @RequestParam(required = false) String startDate,
            @RequestParam(required = false) String endDate,
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "10") int size,
            HttpServletRequest request) {
        checkAdmin(request);
        String token = request.getHeader("token");
        Page<InterviewListResponse> result = interviewService.list(status, keyword, startDate, endDate, page, size, token);
        return ResponseEntity.ok(ApiResponse.success(Map.of(
                "list", result.getContent(),
                "total", result.getTotalElements()
        )));
    }

    /**
     * 记录面试结果
     */
    @PostMapping("/record")
    public ResponseEntity<ApiResponse<InterviewListResponse>> record(
            @Valid @RequestBody InterviewRecordRequest request,
            HttpServletRequest httpRequest) {
        checkAdmin(httpRequest);
        String token = httpRequest.getHeader("token");
        // 从 token 获取当前管理员名称
        String adminName = "admin";
        try {
            HttpHeaders headers = new HttpHeaders();
            headers.set("token", token);
            HttpEntity<Void> entity = new HttpEntity<>(headers);
            ResponseEntity<Map> response = restTemplate.exchange(
                    authServiceUrl + "/api/auth/current",
                    HttpMethod.GET, entity, Map.class);
            if (response.getBody() != null && response.getBody().get("data") != null) {
                @SuppressWarnings("unchecked")
                Map<String, Object> data = (Map<String, Object>) response.getBody().get("data");
                adminName = (String) data.getOrDefault("username", "admin");
            }
        } catch (Exception ignored) {}

        InterviewListResponse result = interviewService.recordInterview(request, adminName, token);
        return ResponseEntity.ok(ApiResponse.success(result));
    }

    /**
     * 更新面试状态（通过/不通过）
     */
    @PutMapping("/{id}/status")
    public ResponseEntity<ApiResponse<InterviewListResponse>> updateStatus(
            @PathVariable Long id,
            @RequestBody Map<String, String> body,
            HttpServletRequest httpRequest) {
        checkAdmin(httpRequest);
        String status = body.get("status");
        if (status == null || status.isEmpty()) {
            throw new RuntimeException("状态不能为空");
        }
        String token = httpRequest.getHeader("token");
        String adminName = "admin";
        try {
            HttpHeaders headers = new HttpHeaders();
            headers.set("token", token);
            HttpEntity<Void> entity = new HttpEntity<>(headers);
            ResponseEntity<Map> response = restTemplate.exchange(
                    authServiceUrl + "/api/auth/current",
                    HttpMethod.GET, entity, Map.class);
            if (response.getBody() != null && response.getBody().get("data") != null) {
                @SuppressWarnings("unchecked")
                Map<String, Object> data = (Map<String, Object>) response.getBody().get("data");
                adminName = (String) data.getOrDefault("username", "admin");
            }
        } catch (Exception ignored) {}

        InterviewListResponse result = interviewService.updateInterviewStatus(id, status, adminName, token);
        return ResponseEntity.ok(ApiResponse.success(result));
    }

    /**
     * 获取面试详情
     */
    @GetMapping("/{enrollmentId}")
    public ResponseEntity<ApiResponse<InterviewListResponse>> detail(
            @PathVariable Long enrollmentId,
            HttpServletRequest request) {
        checkAdmin(request);
        String token = request.getHeader("token");
        InterviewListResponse result = interviewService.getDetail(enrollmentId, token);
        return ResponseEntity.ok(ApiResponse.success(result));
    }

    /**
     * 批量更新面试状态（通过/不通过）
     */
    @PostMapping("/batch-status")
    public ResponseEntity<ApiResponse<Void>> batchUpdateStatus(
            @Valid @RequestBody BatchInterviewStatusRequest request,
            HttpServletRequest httpRequest) {
        checkAdmin(httpRequest);
        String token = httpRequest.getHeader("token");
        String adminName = "admin";
        try {
            HttpHeaders headers = new HttpHeaders();
            headers.set("token", token);
            HttpEntity<Void> entity = new HttpEntity<>(headers);
            ResponseEntity<Map> response = restTemplate.exchange(
                    authServiceUrl + "/api/auth/current",
                    HttpMethod.GET, entity, Map.class);
            if (response.getBody() != null && response.getBody().get("data") != null) {
                @SuppressWarnings("unchecked")
                Map<String, Object> data = (Map<String, Object>) response.getBody().get("data");
                adminName = (String) data.getOrDefault("username", "admin");
            }
        } catch (Exception ignored) {}

        interviewService.batchUpdateStatus(request, adminName, token);
        return ResponseEntity.ok(ApiResponse.success());
    }

    /**
     * 面试统计
     */
    @GetMapping("/statistics")
    public ResponseEntity<ApiResponse<InterviewStatisticsResponse>> statistics(
            HttpServletRequest request) {
        checkAdmin(request);
        return ResponseEntity.ok(ApiResponse.success(interviewService.statistics()));
    }
}
