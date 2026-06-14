package com.open436.auth.entity;

import jakarta.persistence.*;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;
import org.springframework.data.annotation.LastModifiedDate;
import org.springframework.data.jpa.domain.support.AuditingEntityListener;

import java.time.LocalDateTime;

/**
 * 用户统计表
 * 存储用户帖子数、回复数、获赞数、被收藏数
 */
@Entity
@Table(name = "user_statistics")
@Getter
@Setter
@NoArgsConstructor
@EntityListeners(AuditingEntityListener.class)
public class UserStatistics {

    @Id
    @Column(name = "user_id")
    private Long userId;

    @OneToOne(fetch = FetchType.LAZY)
    @MapsId
    @JoinColumn(name = "user_id")
    private UserProfile profile;

    @Column(name = "posts_count", nullable = false)
    private Integer postsCount = 0;

    @Column(name = "replies_count", nullable = false)
    private Integer repliesCount = 0;

    @Column(name = "likes_received", nullable = false)
    private Integer likesReceived = 0;

    @Column(name = "favorites_received", nullable = false)
    private Integer favoritesReceived = 0;

    @LastModifiedDate
    @Column(name = "updated_at", nullable = false)
    private LocalDateTime updatedAt;
}
