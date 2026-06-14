package com.open436.auth.service.impl;

import com.open436.auth.dto.UpdateProfileRequest;
import com.open436.auth.dto.UserProfileResponse;
import com.open436.auth.entity.UserProfile;
import com.open436.auth.entity.UserStatistics;
import com.open436.auth.repository.UserProfileRepository;
import com.open436.auth.repository.UserStatisticsRepository;
import com.open436.auth.service.UserProfileService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.multipart.MultipartFile;

import java.util.Collections;
import java.util.List;
import java.util.stream.Collectors;

@Slf4j
@Service
@RequiredArgsConstructor
public class UserProfileServiceImpl implements UserProfileService {

    private final UserProfileRepository profileRepository;
    private final UserStatisticsRepository statisticsRepository;

    @Override
    public UserProfileResponse getProfile(Long userId) {
        UserProfile profile = profileRepository.findById(userId)
            .orElseThrow(() -> new RuntimeException("用户资料不存在"));
        return UserProfileResponse.from(profile);
    }

    @Override
    @Transactional
    public UserProfileResponse updateProfile(Long userId, UpdateProfileRequest request) {
        UserProfile profile = profileRepository.findById(userId)
            .orElseThrow(() -> new RuntimeException("用户资料不存在"));

        if (request.getNickname() != null) {
            if (!profile.canUpdateNickname()) {
                throw new RuntimeException("昵称30天内只能修改一次");
            }
            profile.setNickname(request.getNickname());
            profile.setNicknameUpdatedAt(java.time.LocalDateTime.now());
        }

        if (request.getBio() != null) {
            profile.setBio(request.getBio());
        }

        if (request.getAvatarUrl() != null) {
            profile.setAvatarUrl(request.getAvatarUrl());
        }

        profileRepository.save(profile);
        return UserProfileResponse.from(profile);
    }

    @Override
    @Transactional
    public String uploadAvatar(Long userId, MultipartFile file) {
        // TODO: 调用 M7 文件服务上传文件，返回 URL
        // 目前直接返回一个占位实现
        UserProfile profile = profileRepository.findById(userId)
            .orElseThrow(() -> new RuntimeException("用户资料不存在"));

        // 实际实现应调用 FileServiceClient
        String avatarUrl = "avatar/" + userId + "/" + file.getOriginalFilename();
        profile.setAvatarUrl(avatarUrl);
        profileRepository.save(profile);
        return avatarUrl;
    }

    @Override
    public List<UserProfileResponse> batchGetProfiles(List<Long> userIds) {
        if (userIds == null || userIds.isEmpty()) {
            return Collections.emptyList();
        }
        List<UserProfile> profiles = profileRepository.findByUserIdIn(userIds);
        return profiles.stream()
            .map(UserProfileResponse::fromSlim)
            .collect(Collectors.toList());
    }

    @Override
    @Transactional
    public void incrementStatistics(Long userId, String field, int value) {
        // 确保统计记录存在
        statisticsRepository.findById(userId).orElseGet(() -> {
            UserProfile profile = profileRepository.findById(userId).orElse(null);
            if (profile == null) return null;
            UserStatistics stats = new UserStatistics();
            stats.setProfile(profile);
            return statisticsRepository.save(stats);
        });

        switch (field) {
            case "posts_count" -> statisticsRepository.incrementPostsCount(userId, value);
            case "replies_count" -> statisticsRepository.incrementRepliesCount(userId, value);
            case "likes_received" -> statisticsRepository.incrementLikesReceived(userId, value);
            case "favorites_received" -> statisticsRepository.incrementFavoritesReceived(userId, value);
            default -> throw new RuntimeException("无效的统计字段: " + field);
        }
    }

    @Override
    @Transactional
    public void createProfileForUser(Long userId, String nickname) {
        if (profileRepository.existsById(userId)) {
            return; // 已存在，不重复创建
        }
        UserProfile profile = new UserProfile();
        profile.setUserId(userId);
        profile.setNickname(nickname != null ? nickname : "用户" + userId);
        profileRepository.save(profile);

        UserStatistics stats = new UserStatistics();
        stats.setProfile(profile);
        statisticsRepository.save(stats);
    }

    @Override
    @Transactional
    public void deleteProfileForUser(Long userId) {
        // FK CASCADE 会自动删除 user_statistics
        profileRepository.deleteById(userId);
    }
}
