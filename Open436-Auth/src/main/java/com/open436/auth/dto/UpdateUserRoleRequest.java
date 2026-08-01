package com.open436.auth.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 更新用户角色请求 DTO
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class UpdateUserRoleRequest {

    /**
     * 角色：admin-管理员，user-用户，viewer-浏览
     */
    @NotBlank(message = "角色不能为空")
    @Pattern(regexp = "^(admin|user|viewer)$", message = "角色值无效")
    private String role;
}
