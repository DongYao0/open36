package com.open436.auth.service;

import com.open436.auth.dto.IncrementStatsRequest;
import com.open436.auth.dto.UpdateProfileRequest;
import com.open436.auth.dto.UserProfileResponse;
import org.springframework.web.multipart.MultipartFile;

import java.util.List;

/**
 * 用户资料服务接口
 */
public interface UserProfileService {

    /**
     * 获取用户资料（含统计）
     */
    UserProfileResponse getProfile(Long userId);

    /**
     * 更新用户资料
     */
    UserProfileResponse updateProfile(Long userId, UpdateProfileRequest request);

    /**
     * 上传头像
     */
    String uploadAvatar(Long userId, MultipartFile file);

    /**
     * 批量获取用户资料（精简版）
     */
    List<UserProfileResponse> batchGetProfiles(List<Long> userIds);

    /**
     * 原子递增统计字段
     */
    void incrementStatistics(Long userId, String field, int value);

    /**
     * 创建用户资料（注册/管理员创建时调用）
     */
    void createProfileForUser(Long userId, String nickname);

    /**
     * 删除用户资料（级联删除统计）
     */
    void deleteProfileForUser(Long userId);
}
