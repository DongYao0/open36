package com.open436.auth.controller;

import com.open436.auth.dto.UpdateProfileRequest;
import com.open436.auth.dto.UserProfileResponse;
import com.open436.auth.service.UserProfileService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.util.HashMap;
import java.util.Map;

/**
 * 用户资料控制器
 * 提供 /api/users/{id}/profile 等端点
 */
@RestController
@RequestMapping("/api/users")
@RequiredArgsConstructor
public class ProfileController {

    private final UserProfileService profileService;

    /**
     * 获取用户资料（公开）
     */
    @GetMapping("/{id}")
    public ResponseEntity<Map<String, Object>> getProfile(@PathVariable Long id) {
        UserProfileResponse profile = profileService.getProfile(id);
        Map<String, Object> response = new HashMap<>();
        response.put("code", 200);
        response.put("message", "success");
        response.put("data", profile);
        return ResponseEntity.ok(response);
    }

    /**
     * 更新用户资料（需登录，本人或管理员）
     */
    @PutMapping("/{id}/profile")
    public ResponseEntity<Map<String, Object>> updateProfile(
            @PathVariable Long id,
            @Valid @RequestBody UpdateProfileRequest request) {
        // TODO: 验证是否是本人或管理员
        UserProfileResponse profile = profileService.updateProfile(id, request);
        Map<String, Object> response = new HashMap<>();
        response.put("code", 200);
        response.put("message", "资料更新成功");
        response.put("data", profile);
        return ResponseEntity.ok(response);
    }

    /**
     * 上传头像
     */
    @PostMapping("/{id}/avatar")
    public ResponseEntity<Map<String, Object>> uploadAvatar(
            @PathVariable Long id,
            @RequestParam("file") MultipartFile file) {
        // TODO: 验证是否是本人或管理员
        String avatarUrl = profileService.uploadAvatar(id, file);
        Map<String, Object> response = new HashMap<>();
        response.put("code", 200);
        response.put("message", "头像上传成功");
        Map<String, Object> data = new HashMap<>();
        data.put("avatar_url", avatarUrl);
        response.put("data", data);
        return ResponseEntity.ok(response);
    }

    /**
     * 获取用户统计（公开）
     */
    @GetMapping("/{id}/statistics")
    public ResponseEntity<Map<String, Object>> getStatistics(@PathVariable Long id) {
        UserProfileResponse profile = profileService.getProfile(id);
        Map<String, Object> response = new HashMap<>();
        response.put("code", 200);
        response.put("message", "success");
        response.put("data", profile.getStatistics());
        return ResponseEntity.ok(response);
    }
}
