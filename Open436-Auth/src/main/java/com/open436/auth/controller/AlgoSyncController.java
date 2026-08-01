package com.open436.auth.controller;

import cn.dev33.satoken.annotation.SaCheckLogin;
import com.open436.auth.dto.AlgoSyncRequest;
import com.open436.auth.dto.ApiResponse;
import com.open436.auth.service.AlgoSyncService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

/**
 * 算法系统同步控制器
 * 负责将当前登录用户同步到 HOJ（在线评测系统）
 */
@Slf4j
@RestController
@RequestMapping("/api/auth")
@RequiredArgsConstructor
public class AlgoSyncController {

    private final AlgoSyncService algoSyncService;

    /**
     * 同步当前用户到 HOJ，获取 HOJ 的 JWT Token
     */
    @PostMapping("/algo-sync")
    @SaCheckLogin
    public ResponseEntity<ApiResponse<String>> syncToHoj(
            @RequestBody(required = false) AlgoSyncRequest request) {
        log.info("算法系统同步请求");

        ApiResponse<String> response = algoSyncService.syncToHoj(request);

        if (response.getCode() == 200) {
            return ResponseEntity.ok(response);
        } else {
            return ResponseEntity.status(500).body(response);
        }
    }
}
