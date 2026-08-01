package com.open436.enrollment.entity;

import jakarta.persistence.*;
import lombok.*;
import org.hibernate.annotations.CreationTimestamp;

import java.time.LocalDateTime;

@Entity
@Table(name = "enrollment_applications")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class EnrollmentApplication {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    /**
     * 关联 Auth 服务 users_auth.id — 唯一可信用户数据源
     * 用户名、姓名、学号、手机号、专业等信息均从 Auth 服务查询
     */
    @Column(name = "auth_user_id", unique = true)
    private Long authUserId;

    @Column(name = "self_intro", columnDefinition = "TEXT")
    private String selfIntro;

    @Column(length = 500)
    private String skills;

    @Column(nullable = false, length = 20)
    @Builder.Default
    private String status = "pending";

    @CreationTimestamp
    @Column(name = "submitted_at", nullable = false, updatable = false)
    private LocalDateTime submittedAt;

    @Column(name = "reviewed_at")
    private LocalDateTime reviewedAt;

    @Column(name = "reviewed_by", length = 50)
    private String reviewedBy;

    @Column(name = "review_reason", columnDefinition = "TEXT")
    private String reviewReason;
}
