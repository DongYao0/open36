package com.open436.enrollment.exception;

/**
 * 报名链路可重试失败（阶段5.5）：
 * Auth 网络超时/不可达。行内已置 RETRYABLE_FAILED，
 * 用户以同一幂等键重试可恢复；映射 HTTP 503 + 明确提示。
 */
public class EnrollRetryableException extends RuntimeException {

    public EnrollRetryableException(String message) {
        super(message);
    }
}
