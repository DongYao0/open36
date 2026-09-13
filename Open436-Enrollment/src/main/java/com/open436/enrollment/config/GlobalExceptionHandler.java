package com.open436.enrollment.config;

import com.open436.enrollment.dto.ApiResponse;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.FieldError;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

import java.util.stream.Collectors;

@Slf4j
@RestControllerAdvice
public class GlobalExceptionHandler {

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<ApiResponse<Void>> handleValidation(MethodArgumentNotValidException e) {
        String msg = e.getBindingResult().getFieldErrors().stream()
                .map(FieldError::getDefaultMessage)
                .collect(Collectors.joining(", "));
        return ResponseEntity.badRequest().body(ApiResponse.error(400, msg));
    }

    @ExceptionHandler(com.open436.enrollment.exception.EnrollConflictException.class)
    public ResponseEntity<ApiResponse<Void>> handleEnrollConflict(
            com.open436.enrollment.exception.EnrollConflictException e) {
        log.warn("报名冲突: {}", e.getMessage());
        return ResponseEntity.status(HttpStatus.CONFLICT)
                .body(ApiResponse.error(409, e.getMessage()));
    }

    @ExceptionHandler(com.open436.enrollment.exception.EnrollRetryableException.class)
    public ResponseEntity<ApiResponse<Void>> handleEnrollRetryable(
            com.open436.enrollment.exception.EnrollRetryableException e) {
        log.warn("报名暂时不可用(可重试): {}", e.getMessage());
        return ResponseEntity.status(HttpStatus.SERVICE_UNAVAILABLE)
                .header("Retry-After", "5")
                .body(ApiResponse.error(503, e.getMessage()));
    }

    @ExceptionHandler(org.springframework.dao.DataIntegrityViolationException.class)
    public ResponseEntity<ApiResponse<Void>> handleDataIntegrity(
            org.springframework.dao.DataIntegrityViolationException e) {
        // 唯一约束竞争是并发下的正常路径，不得以 500 暴露（阶段5.5）
        log.warn("报名唯一约束竞争: {}", e.getMostSpecificCause().getMessage());
        return ResponseEntity.status(HttpStatus.CONFLICT)
                .body(ApiResponse.error(409, "请求重复提交，请刷新查看报名结果"));
    }

    @ExceptionHandler(RuntimeException.class)
    public ResponseEntity<ApiResponse<Void>> handleRuntime(RuntimeException e) {
        log.warn("业务异常: {}", e.getMessage());
        return ResponseEntity.badRequest().body(ApiResponse.error(400, e.getMessage()));
    }

    @ExceptionHandler(Exception.class)
    public ResponseEntity<ApiResponse<Void>> handleException(Exception e) {
        log.error("系统异常", e);
        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                .body(ApiResponse.error(500, "系统错误，请稍后重试"));
    }
}
