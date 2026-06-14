package com.open436.auth.entity;

import jakarta.persistence.*;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;
import org.springframework.data.annotation.CreatedDate;
import org.springframework.data.annotation.LastModifiedDate;
import org.springframework.data.jpa.domain.support.AuditingEntityListener;

import java.time.LocalDateTime;
import java.time.temporal.ChronoUnit;

/**
 * 用户资料表
 * 存储用户昵称、头像、简介等社交信息
 */
@Entity
@Table(name = "users_profile")
@Getter
@Setter
@NoArgsConstructor
@EntityListeners(AuditingEntityListener.class)
public class UserProfile {

    @Id
    @Column(name = "user_id")
    private Long userId;

    @Column(nullable = false, length = 20)
    private String nickname;

    @Column(name = "avatar_url", length = 500)
    private String avatarUrl;

    @Column(columnDefinition = "TEXT")
    private String bio;

    @Column(name = "nickname_updated_at")
    private LocalDateTime nicknameUpdatedAt;

    @CreatedDate
    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    @LastModifiedDate
    @Column(name = "updated_at", nullable = false)
    private LocalDateTime updatedAt;

    @OneToOne(mappedBy = "profile", cascade = CascadeType.ALL, fetch = FetchType.LAZY)
    private UserStatistics statistics;

    /**
     * 检查是否可以修改昵称（30天限制）
     */
    public boolean canUpdateNickname() {
        if (nicknameUpdatedAt == null) return true;
        return ChronoUnit.DAYS.between(nicknameUpdatedAt, LocalDateTime.now()) >= 30;
    }
}
