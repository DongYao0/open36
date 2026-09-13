package com.open436.enrollment.service;

import com.open436.enrollment.entity.EnrollmentApplication;
import com.open436.enrollment.repository.EnrollmentRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.ResponseEntity;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;

/**
 * 报名对账任务（阶段5.3）
 *
 * 每分钟扫描滞留超过 10 分钟的中间态报名：
 *   CREATING_USER → 问 Auth“这个幂等键建号成功了吗？”
 *                    成功 → 回填 userId 落 PENDING（修复半成功）；
 *                    否则 → RETRYABLE_FAILED 等用户重试；
 *   USER_CREATED  → 直接补写终态（仅剩本地落库）；
 *   RECEIVED      → 请求体（密码）不可恢复 → RETRYABLE_FAILED。
 *
 * 安全边界：只处理 pending 用户（Auth 幂等键查询/建号永远是 pending），
 * 绝不删除或激活任何用户；对账失败记 error 日志即视为告警。
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class EnrollmentReconciliationService {

    private final EnrollmentRepository enrollmentRepository;
    private final RestTemplate enrollmentRestTemplate;

    @Value("${auth.service.url:http://localhost:8081}")
    private String authServiceUrl;

    @Value("${internal.api-key:}")
    private String internalApiKey;

    /** 中间态滞留阈值（分钟） */
    private static final int STUCK_MINUTES = 10;

    @Scheduled(fixedDelay = 60_000, initialDelay = 90_000)
    public void reconcileStuckEnrollments() {
        LocalDateTime threshold = LocalDateTime.now().minusMinutes(STUCK_MINUTES);
        List<EnrollmentApplication> stuck = enrollmentRepository.findStuckIntermediate(threshold);
        if (stuck.isEmpty()) {
            return;
        }
        log.warn("对账：发现 {} 条滞留报名（>{}分钟），开始恢复", stuck.size(), STUCK_MINUTES);
        for (EnrollmentApplication row : stuck) {
            try {
                reconcileOne(row);
            } catch (Exception e) {
                // 单行失败不阻断批次；error 日志即告警信号（阶段11监控抓取）
                log.error("对账失败: id={}, idemKey={}, error={}",
                        row.getId(),
                        row.getIdempotencyKey() != null && row.getIdempotencyKey().length() > 8
                                ? row.getIdempotencyKey().substring(0, 8) : "short",
                        e.getMessage());
            }
        }
    }

    private void reconcileOne(EnrollmentApplication row) {
        switch (row.getProcessingStatus()) {
            case EnrollmentApplication.PS_CREATING_USER -> {
                Long userId = lookupAuthUserId(row.getIdempotencyKey());
                if (userId != null) {
                    row.setAuthUserId(userId);
                    row.setProcessingStatus(EnrollmentApplication.PS_PENDING);
                    row.setLastError(null);
                    enrollmentRepository.save(row);
                    log.info("对账恢复：Auth已建号，报名落终态 id={} authUserId={}", row.getId(), userId);
                } else {
                    markRetryable(row, "网络中断，请使用原页面重试报名");
                }
            }
            case EnrollmentApplication.PS_USER_CREATED -> {
                row.setProcessingStatus(EnrollmentApplication.PS_PENDING);
                row.setLastError(null);
                enrollmentRepository.save(row);
                log.info("对账恢复：补写终态 id={} authUserId={}", row.getId(), row.getAuthUserId());
            }
            case EnrollmentApplication.PS_RECEIVED -> {
                // 未发出注册请求（进程崩溃）：请求体不可恢复
                markRetryable(row, "提交中断，请重新提交报名信息");
            }
            default -> { /* 其他状态不在对账范围 */ }
        }
    }

    /** 查询 Auth 幂等注册结果；网络异常时返回 null（下轮再试） */
    private Long lookupAuthUserId(String idempotencyKey) {
        if (idempotencyKey == null) {
            return null;
        }
        try {
            HttpHeaders headers = new HttpHeaders();
            headers.set("X-Internal-API-Key", internalApiKey);
            ResponseEntity<Map> response = enrollmentRestTemplate.exchange(
                    authServiceUrl + "/internal/users/registrations/by-key/" + idempotencyKey,
                    HttpMethod.GET, new HttpEntity<>(headers), Map.class);
            if (!response.getStatusCode().is2xxSuccessful() || response.getBody() == null) {
                return null;
            }
            Map<String, Object> data = (Map<String, Object>) response.getBody().get("data");
            if (data == null || !"SUCCEEDED".equals(data.get("status"))) {
                return null;
            }
            Number userId = (Number) data.get("userId");
            return userId != null ? userId.longValue() : null;
        } catch (Exception e) {
            log.warn("对账查询Auth失败（下轮重试）: error={}", e.getMessage());
            return null;
        }
    }

    private void markRetryable(EnrollmentApplication row, String reason) {
        row.setProcessingStatus(EnrollmentApplication.PS_RETRYABLE_FAILED);
        row.setLastError(reason);
        enrollmentRepository.save(row);
        log.warn("对账标记可重试: id={}, reason={}", row.getId(), reason);
    }
}
