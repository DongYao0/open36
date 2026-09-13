package com.open436.enrollment.exception;

/**
 * 报名链路确定性冲突（阶段5.5）：
 * 同幂等键内容漂移 / 用户名真实冲突 / 已报名 / 幂等键处理中。
 * 一律映射 HTTP 409，绝不以 500 形式暴露。
 */
public class EnrollConflictException extends RuntimeException {

    public EnrollConflictException(String message) {
        super(message);
    }
}
