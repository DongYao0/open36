package com.open436.auth.entity;

import jakarta.persistence.*;
import lombok.*;

import java.time.LocalDateTime;

/**
 * 注册幂等记录（阶段5.2）
 *
 * 同一 X-Idempotency-Key 的注册请求：
 *   - 已成功 → 事务内直接返回原 user_id，不重复建号；
 *   - 同 Key 不同内容（fingerprint 不符）→ 409；
 *   - 并发同 Key → pg_advisory_xact_lock 串行化，后到者读到成功结果。
 *
 * 表内绝不存明文密码或其摘要：fingerprint 仅覆盖身份字段。
 */
@Entity
@Table(name = "auth_registration_records")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class RegistrationRecord {

    public static final String STATUS_PROCESSING = "PROCESSING";
    public static final String STATUS_SUCCEEDED = "SUCCEEDED";
    public static final String STATUS_FAILED = "FAILED";

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "idempotency_key", nullable = false, length = 64, unique = true)
    private String idempotencyKey;

    @Column(name = "request_fingerprint", nullable = false, length = 64)
    private String requestFingerprint;

    /** 注册成功后回填；失败前为空 */
    @Column(name = "user_id")
    private Long userId;

    /** PROCESSING / SUCCEEDED / FAILED */
    @Column(nullable = false, length = 20)
    @Builder.Default
    private String status = STATUS_PROCESSING;

    @Column(name = "created_at", nullable = false, updatable = false)
    @Builder.Default
    private LocalDateTime createdAt = LocalDateTime.now();

    @Column(name = "updated_at", nullable = false)
    @Builder.Default
    private LocalDateTime updatedAt = LocalDateTime.now();
}
