package com.open436.auth.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 更新用户客户端权限请求 DTO
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class UpdateUserPermissionRequest {

    /**
     * 客户端使用权限（all/forum/algo/none），algo 为算法管理权限
     */
    @NotBlank(message = "权限不能为空")
    @Pattern(regexp = "^(all|forum|algo|none)$", message = "权限只能是 all、forum、algo 或 none")
    private String clientPermission;
}
