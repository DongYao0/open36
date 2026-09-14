package com.open436.auth.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 用户注册请求 DTO
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class RegisterRequest {

    /**
     * 用户名（3-20字符）
     */
    @NotBlank(message = "用户名不能为空")
    @Size(min = 1, max = 20, message = "用户名长度必须为1-20个字符")
    private String username;

    /**
     * 密码（6-32字符）
     */
    @NotBlank(message = "密码不能为空")
    @Size(min = 6, max = 32, message = "密码长度必须为6-32个字符")
    private String password;

    /**
     * 昵称（可选）
     */
    private String nickname;

    /**
     * 学号
     */
    @NotBlank(message = "学号不能为空")
    @Pattern(regexp = "^20\\d{10}$", message = "学号必须为20开头的12位数字")
    private String studentId;

    /**
     * 真实姓名
     */
    @NotBlank(message = "真实姓名不能为空")
    @Pattern(regexp = "^[\\u4e00-\\u9fff]{2,20}$", message = "真实姓名必须为2-20个中文字符")
    private String realName;

    /**
     * 电话号码
     */
    private String phone;

    /**
     * 专业
     */
    @NotBlank(message = "专业不能为空")
    @Pattern(regexp = "^[\\u4e00-\\u9fff]{2,100}$", message = "专业必须为中文")
    private String major;
}
