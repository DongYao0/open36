package com.open436.auth.service;

import com.open436.auth.dto.AlgoSyncRequest;
import com.open436.auth.dto.ApiResponse;

/**
 * 算法系统同步服务
 * 负责与 HOJ 进行用户同步（SSO）
 */
public interface AlgoSyncService {

    /**
     * 同步当前登录用户到 HOJ，返回 HOJ 的 JWT Token
     * @param request 同步请求（可选字段）
     * @return HOJ Token
     */
    ApiResponse<String> syncToHoj(AlgoSyncRequest request);

    /**
     * 同步指定用户到 HOJ（不依赖当前 Session，供跨服务调用）
     * @param username 用户名
     * @param nickname 昵称
     * @param role 角色
     * @return HOJ Token
     */
    ApiResponse<String> syncUserToHoj(String username, String nickname, String role);

    /**
     * 同步指定用户到 HOJ 并保存映射关系
     * @param authUserId Open436 用户ID
     * @param username 用户名
     * @param nickname 昵称
     * @param role 角色
     * @return HOJ Token
     */
    ApiResponse<String> syncUserToHoj(Long authUserId, String username, String nickname, String role);
}
