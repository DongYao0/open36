package com.open436.auth.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 登录请求 DTO
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class LoginRequest {
    
    /**
     * 用户名（2-20字符，报名时即真实姓名）
     */
    @NotBlank(message = "用户名不能为空")
    @Size(min = 2, max = 20, message = "用户名长度必须为2-20个字符")
    private String username;
    
    /**
     * 密码（6-32字符）
     */
    @NotBlank(message = "密码不能为空")
    @Size(min = 6, max = 32, message = "密码长度必须为6-32个字符")
    private String password;
    
    /**
     * 是否记住我（可选）
     */
    private Boolean rememberMe = false;
}

