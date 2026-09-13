package com.open436.auth.service;

import com.open436.auth.dto.CreateUserRequest;
import com.open436.auth.dto.RegisterRequest;
import com.open436.auth.dto.UserInfoResponse;
import com.open436.auth.entity.RegistrationRecord;
import com.open436.auth.enums.ErrorCode;
import com.open436.auth.exception.BusinessException;
import com.open436.auth.repository.RegistrationRecordRepository;
import com.open436.auth.repository.UserAuthRepository;
import com.open436.auth.service.impl.UserServiceImpl;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.HexFormat;

/**
 * 幂等注册服务（阶段5.2）
 *
 * 与 UserServiceImpl.createUser 的区别：围绕 X-Idempotency-Key 建立同事务
 * 的"锁记录→建号→回填"闭环，供 Enrollment 报名链路调用：
 *
 *   1. pg_advisory_xact_lock(key) 串行化同 Key 并发；
 *   2. 已成功   → 返回原 user（不重建）；
 *      内容漂移 → 409；
 *      处理中   → 409（稍后重试）；
 *      曾失败   → 清记录重走建号；
 *   3. createUser（pending 用户）；
 *   4. 回填 SUCCEEDED + user_id，随事务提交。
 *
 * 日志与记录表均不含明文密码；fingerprint 只覆盖身份字段。
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class RegistrationService {

    private final RegistrationRecordRepository recordRepository;
    private final UserAuthRepository userAuthRepository;
    private final UserServiceImpl userService;

    /** 身份字段指纹（不含密码）：同 Key 内容漂移检测 */
    public static String fingerprint(RegisterRequest request) {
        String material = String.join("|",
                nullSafe(request.getUsername()).toLowerCase(),
                nullSafe(request.getStudentId()),
                nullSafe(request.getRealName()),
                nullSafe(request.getPhone()),
                nullSafe(request.getMajor()));
        return sha256(material);
    }

    @Transactional
    public UserInfoResponse registerIdempotent(RegisterRequest request, String idempotencyKey) {
        String fingerprint = fingerprint(request);

        // 1. 同 Key 串行化：后到的事务等首个提交后再读记录
        recordRepository.acquireAdvisoryLock(idempotencyKey);

        RegistrationRecord record = recordRepository.findByIdempotencyKey(idempotencyKey).orElse(null);

        if (record != null && RegistrationRecord.STATUS_SUCCEEDED.equals(record.getStatus())) {
            if (!record.getRequestFingerprint().equals(fingerprint)) {
                // 同 Key 提交了不同身份内容：不得复用旧结果
                throw new BusinessException(ErrorCode.IDEMPOTENCY_CONFLICT,
                        "幂等键与请求内容不匹配，请刷新页面重新提交");
            }
            return userAuthRepository.findById(record.getUserId())
                    .map(u -> UserInfoResponse.builder()
                            .id(u.getId()).username(u.getUsername())
                            .role("user").status(u.getStatus()).build())
                    .orElseThrow(() -> new BusinessException(ErrorCode.USER_NOT_FOUND));
        }

        if (record != null && RegistrationRecord.STATUS_PROCESSING.equals(record.getStatus())) {
            // 前一事务仍在处理（理论上 advisory lock 下不应出现，防御上游超时残留）
            throw new BusinessException(ErrorCode.IDEMPOTENCY_IN_PROGRESS,
                    "相同的注册请求正在处理中，请稍候重试");
        }

        if (record == null) {
            record = RegistrationRecord.builder()
                    .idempotencyKey(idempotencyKey)
                    .requestFingerprint(fingerprint)
                    .status(RegistrationRecord.STATUS_PROCESSING)
                    .build();
        } else {
            // FAILED → 重试：复用行，重置状态
            record.setStatus(RegistrationRecord.STATUS_PROCESSING);
            record.setUserId(null);
            record.setUpdatedAt(java.time.LocalDateTime.now());
        }
        record = recordRepository.saveAndFlush(record);

        // 2. 创建 pending 用户（同事务；用户名真实冲突 → USERNAME_EXISTS 409）
        UserInfoResponse created = userService.createUser(toCreateRequest(request));

        // 3. 回填成功结果，随本事务提交
        record.setUserId(created.getId());
        record.setStatus(RegistrationRecord.STATUS_SUCCEEDED);
        record.setUpdatedAt(java.time.LocalDateTime.now());
        recordRepository.save(record);

        log.info("幂等注册完成: idemKey={}, userId={}, username={}",
                idemKey(idempotencyKey), created.getId(), created.getUsername());
        return created;
    }

    /** 供 Enrollment 对账：按 Key 查询注册结果（不暴露密码等敏感字段） */
    @Transactional(readOnly = true)
    public RegistrationLookup lookupByIdempotencyKey(String idempotencyKey) {
        return recordRepository.findByIdempotencyKey(idempotencyKey)
                .map(r -> new RegistrationLookup(r.getStatus(), r.getUserId()))
                .orElse(null);
    }

    public record RegistrationLookup(String status, Long userId) {}

    /** 日志脱敏：只留前 8 位用于关联 */
    private static String idemKey(String key) {
        return key.length() <= 8 ? "short" : key.substring(0, 8);
    }

    private static CreateUserRequest toCreateRequest(RegisterRequest request) {
        CreateUserRequest createRequest = new CreateUserRequest();
        createRequest.setUsername(request.getUsername());
        createRequest.setPassword(request.getPassword());
        createRequest.setRole("user");
        createRequest.setStatus("pending");
        createRequest.setStudentId(request.getStudentId());
        createRequest.setRealName(request.getRealName());
        createRequest.setPhone(request.getPhone());
        createRequest.setMajor(request.getMajor());
        return createRequest;
    }

    private static String nullSafe(String value) {
        return value == null ? "" : value.trim();
    }

    private static String sha256(String input) {
        try {
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            return HexFormat.of().formatHex(digest.digest(input.getBytes(StandardCharsets.UTF_8)));
        } catch (Exception e) {
            throw new IllegalStateException("SHA-256 unavailable", e);
        }
    }
}
