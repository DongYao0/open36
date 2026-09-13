package com.open436.auth.controller;

import com.open436.auth.dto.BatchUserRequest;
import com.open436.auth.dto.IncrementStatsRequest;
import com.open436.auth.dto.UserProfileResponse;
import com.open436.auth.service.RegistrationService;
import com.open436.auth.service.UserProfileService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * 内部用户控制器（供其他微服务调用）
 * 通过 X-Internal-API-Key 校验调用方身份，防止外部直连绕过网关
 */
@RestController
@RequestMapping("/internal/users")
@RequiredArgsConstructor
public class InternalUserController {

    private final UserProfileService profileService;
    private final RegistrationService registrationService;

    @Value("${internal.api-key}")
    private String internalApiKey;

    /**
     * 校验内部调用密钥（常量时间比较防时序攻击）
     */
    private void verifyInternalKey(String providedKey) {
        if (providedKey == null || !constantTimeEquals(internalApiKey, providedKey)) {
            throw new SecurityException("Invalid internal API key");
        }
    }

    private boolean constantTimeEquals(String a, String b) {
        if (a == null || b == null || a.length() != b.length()) {
            return false;
        }
        int result = 0;
        for (int i = 0; i < a.length(); i++) {
            result |= a.charAt(i) ^ b.charAt(i);
        }
        return result == 0;
    }

    /**
     * 批量获取用户资料
     */
    @PostMapping("/batch")
    public ResponseEntity<Map<String, Object>> batchGetProfiles(
            @RequestHeader(value = "X-Internal-API-Key", required = false) String internalKey,
            @Valid @RequestBody BatchUserRequest request) {
        verifyInternalKey(internalKey);
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
     * 按幂等键查询注册结果（阶段5.3：Enrollment 对账用）
     * 返回 {status: SUCCEEDED|PROCESSING|FAILED|null, userId}
     * 不返回任何身份字段或密码材料。
     */
    @GetMapping("/registrations/by-key/{idempotencyKey}")
    public ResponseEntity<Map<String, Object>> lookupRegistration(
            @RequestHeader(value = "X-Internal-API-Key", required = false) String internalKey,
            @PathVariable String idempotencyKey) {
        verifyInternalKey(internalKey);
        RegistrationService.RegistrationLookup lookup =
                registrationService.lookupByIdempotencyKey(idempotencyKey);
        Map<String, Object> response = new HashMap<>();
        response.put("code", 200);
        response.put("message", "success");
        Map<String, Object> data = new HashMap<>();
        if (lookup != null) {
            data.put("status", lookup.status());
            data.put("userId", lookup.userId());
        }
        response.put("data", data);
        return ResponseEntity.ok(response);
    }

    /**
     * 原子递增统计字段
     */
    @PostMapping("/{id}/statistics/increment")
    public ResponseEntity<Map<String, Object>> incrementStatistics(
            @RequestHeader(value = "X-Internal-API-Key", required = false) String internalKey,
            @PathVariable Long id,
            @Valid @RequestBody IncrementStatsRequest request) {
        verifyInternalKey(internalKey);
        profileService.incrementStatistics(id, request.getField(), request.getValue());
        Map<String, Object> response = new HashMap<>();
        response.put("code", 200);
        response.put("message", "统计已更新");
        return ResponseEntity.ok(response);
    }
}
