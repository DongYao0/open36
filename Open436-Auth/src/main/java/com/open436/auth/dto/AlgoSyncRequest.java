package com.open436.auth.dto;

import lombok.Data;

/**
 * 算法系统同步请求 DTO
 */
@Data
public class AlgoSyncRequest {

    /**
     * 用户昵称（可选，用于同步到 HOJ）
     */
    private String nickname;

    /**
     * 用户头像（可选，用于同步到 HOJ）
     */
    private String avatar;
}
