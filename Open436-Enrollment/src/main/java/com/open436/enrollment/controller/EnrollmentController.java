package com.open436.enrollment.controller;

import com.open436.enrollment.dto.*;
import com.open436.enrollment.service.EnrollmentService;
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

import java.util.List;
import java.util.Map;

@Slf4j
@RestController
@RequestMapping("/api/enrollment")
@RequiredArgsConstructor
public class EnrollmentController {

    private final EnrollmentService enrollmentService;
    private final RestTemplate restTemplate = new RestTemplate();

    @Value("${auth.service.url:http://localhost:8081}")
    private String authServiceUrl;

    private String checkAdmin(HttpServletRequest request) {
        String token = request.getHeader("token");
        log.info("[DEBUG] checkAdmin received token: {}", token);
        if (token == null || token.isEmpty()) {
            throw new RuntimeException("未登录");
        }
        HttpHeaders headers = new HttpHeaders();
        headers.set("token", token);
        HttpEntity<Void> entity = new HttpEntity<>(headers);
        try {
            ResponseEntity<Map> response = restTemplate.exchange(
                    authServiceUrl + "/api/auth/current",
                    HttpMethod.GET,
                    entity,
                    Map.class
            );
            Map<String, Object> body = response.getBody();
            if (body == null || body.get("data") == null) {
                throw new RuntimeException("鉴权失败");
            }
            Map<String, Object> data = (Map<String, Object>) body.get("data");
            String role = (String) data.get("role");
            if (!"admin".equals(role)) {
                throw new RuntimeException("无管理员权限");
            }
            return (String) data.get("username");
        } catch (RuntimeException e) {
            throw e;
        } catch (Exception e) {
            throw new RuntimeException("鉴权失败: " + e.getMessage());
        }
    }

    @PostMapping("/apply")
    public ResponseEntity<ApiResponse<Void>> apply(@Valid @RequestBody ApplyRequest request) {
        log.info("报名申请: username={}", request.getUsername());
        enrollmentService.apply(request);
        return ResponseEntity.ok(ApiResponse.success());
    }

    @GetMapping("/")
    public ResponseEntity<ApiResponse<Map<String, Object>>> list(
            @RequestParam(required = false) String status,
            @RequestParam(required = false) String keyword,
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "10") int size,
            HttpServletRequest request) {
        checkAdmin(request);
        String token = request.getHeader("token");
        Page<ApplicationListResponse> result = enrollmentService.list(status, keyword, page, size, token);
        return ResponseEntity.ok(ApiResponse.success(Map.of(
                "list", result.getContent(),
                "total", result.getTotalElements()
        )));
    }

    @PutMapping("/{id}/review")
    public ResponseEntity<ApiResponse<ApplicationListResponse>> review(
            @PathVariable Long id,
            @Valid @RequestBody ReviewRequest request,
            HttpServletRequest httpRequest) {
        String adminName = checkAdmin(httpRequest);
        String token = httpRequest.getHeader("token");
        ApplicationListResponse response = enrollmentService.review(id, request, adminName, token);
        return ResponseEntity.ok(ApiResponse.success(response));
    }

    @PostMapping("/batch-review")
    public ResponseEntity<ApiResponse<Void>> batchReview(
            @Valid @RequestBody BatchReviewRequest request,
            HttpServletRequest httpRequest) {
        String adminName = checkAdmin(httpRequest);
        String token = httpRequest.getHeader("token");
        enrollmentService.batchReview(request, adminName, token);
        return ResponseEntity.ok(ApiResponse.success());
    }

    @GetMapping("/statistics")
    public ResponseEntity<ApiResponse<StatisticsResponse>> statistics(HttpServletRequest request) {
        checkAdmin(request);
        return ResponseEntity.ok(ApiResponse.success(enrollmentService.statistics()));
    }
}
