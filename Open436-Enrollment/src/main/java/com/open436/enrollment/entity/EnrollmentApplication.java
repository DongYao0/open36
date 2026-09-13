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

    /** 写入路径状态机常量（阶段5.3） */
    public static final String PS_RECEIVED = "RECEIVED";
    public static final String PS_CREATING_USER = "CREATING_USER";
    public static final String PS_USER_CREATED = "USER_CREATED";
    public static final String PS_PENDING = "PENDING";
    public static final String PS_RETRYABLE_FAILED = "RETRYABLE_FAILED";
    public static final String PS_PERMANENT_FAILED = "PERMANENT_FAILED";

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    /**
     * 关联 Auth 服务 users_auth.id — 唯一可信用户数据源
     * 用户名、姓名、学号、手机号、专业等信息均从 Auth 服务查询
     */
    @Column(name = "auth_user_id")
    private Long authUserId;

    /**
     * 报名幂等键（前端每次报名表单会话生成 UUID，重试复用）。
     * 数据库部分唯一索引兜底并发重复提交；存量行允许为 NULL。
     */
    @Column(name = "idempotency_key", length = 64)
    private String idempotencyKey;

    /** 身份+报名内容指纹（SHA-256）：同 Key 不同内容 → 409 */
    @Column(name = "request_fingerprint", length = 64)
    private String requestFingerprint;

    /**
     * 写入路径状态机（与审核态 status 正交）：
     * RECEIVED → CREATING_USER → USER_CREATED → PENDING
     * 失败：RETRYABLE_FAILED / PERMANENT_FAILED
     */
    @Column(name = "processing_status", nullable = false, length = 30)
    @Builder.Default
    private String processingStatus = "RECEIVED";

    /** 最近一次失败原因（不含密码） */
    @Column(name = "last_error", columnDefinition = "TEXT")
    private String lastError;

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
