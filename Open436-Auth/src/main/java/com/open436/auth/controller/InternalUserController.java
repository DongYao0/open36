package com.open436.auth.controller;

import com.open436.auth.dto.BatchUserRequest;
import com.open436.auth.dto.IncrementStatsRequest;
import com.open436.auth.dto.UserProfileResponse;
import com.open436.auth.service.UserProfileService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * 内部用户控制器（供其他微服务调用）
 */
@RestController
@RequestMapping("/internal/users")
@RequiredArgsConstructor
public class InternalUserController {

    private final UserProfileService profileService;

    /**
     * 批量获取用户资料
     */
    @PostMapping("/batch")
    public ResponseEntity<Map<String, Object>> batchGetProfiles(@Valid @RequestBody BatchUserRequest request) {
        List<UserProfileResponse> profiles = profileService.batchGetProfiles(request.getUserIds());
        Map<String, Object> response = new HashMap<>();
        response.put("code", 200);
        response.put("message", "success");
        Map<String, Object> data = new HashMap<>();
        data.put("users", profiles);
        response.put("data", data);
        return ResponseEntity.ok(response);
    }

    /**
     * 原子递增统计字段
     */
    @PostMapping("/{id}/statistics/increment")
    public ResponseEntity<Map<String, Object>> incrementStatistics(
            @PathVariable Long id,
            @Valid @RequestBody IncrementStatsRequest request) {
        profileService.incrementStatistics(id, request.getField(), request.getValue());
        Map<String, Object> response = new HashMap<>();
        response.put("code", 200);
        response.put("message", "统计已更新");
        return ResponseEntity.ok(response);
    }
}
