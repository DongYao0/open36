package com.open436.auth.entity;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;
import org.hibernate.annotations.CreationTimestamp;

import java.time.LocalDateTime;

/**
 * Open436 用户与 HOJ 用户的映射表
 * 解决 username 变更导致的 HOJ 关联失效问题
 */
@Entity
@Table(name = "hoj_user_mapping")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
public class HojUserMapping {

    /**
     * Open436 用户ID（主键，与 users_auth.id 一对一）
     */
    @Id
    @Column(name = "auth_user_id", nullable = false)
    private Long authUserId;

    /**
     * HOJ 用户 UUID
     */
    @Column(name = "hoj_uuid", nullable = false, length = 32)
    private String hojUuid;

    /**
     * 创建时间
     */
    @CreationTimestamp
    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;
}
