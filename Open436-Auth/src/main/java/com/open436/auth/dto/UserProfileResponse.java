package com.open436.auth.dto;

import com.open436.auth.entity.UserProfile;
import com.open436.auth.entity.UserStatistics;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

/**
 * 用户资料响应 DTO
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class UserProfileResponse {

    private Long userId;
    private String nickname;
    private String avatarUrl;
    private String bio;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
    private StatisticsData statistics;

    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class StatisticsData {
        private Integer postsCount;
        private Integer repliesCount;
        private Integer likesReceived;
        private Integer favoritesReceived;
    }

    public static UserProfileResponse from(UserProfile profile) {
        StatisticsData stats = null;
        UserStatistics s = profile.getStatistics();
        if (s != null) {
            stats = StatisticsData.builder()
                .postsCount(s.getPostsCount())
                .repliesCount(s.getRepliesCount())
                .likesReceived(s.getLikesReceived())
                .favoritesReceived(s.getFavoritesReceived())
                .build();
        }
        return UserProfileResponse.builder()
            .userId(profile.getUserId())
            .nickname(profile.getNickname())
            .avatarUrl(profile.getAvatarUrl())
            .bio(profile.getBio())
            .createdAt(profile.getCreatedAt())
            .updatedAt(profile.getUpdatedAt())
            .statistics(stats)
            .build();
    }

    /**
     * 精简版（用于批量查询）
     */
    public static UserProfileResponse fromSlim(UserProfile profile) {
        return UserProfileResponse.builder()
            .userId(profile.getUserId())
            .nickname(profile.getNickname())
            .avatarUrl(profile.getAvatarUrl())
            .build();
    }
}
