package com.open436.enrollment.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;
import lombok.Data;

@Data
public class ApplyRequest {

    @NotBlank(message = "用户名不能为空")
    @Size(min = 1, max = 20, message = "用户名长度必须为1-20个字符")
    private String username;

    @NotBlank(message = "密码不能为空")
    @Size(min = 6, max = 32, message = "密码长度必须为6-32个字符")
    private String password;

    @NotBlank(message = "真实姓名不能为空")
    @Pattern(regexp = "^[\\u4e00-\\u9fff]{2,20}$", message = "真实姓名必须为2-20个中文字符")
    private String realName;

    @NotBlank(message = "学号不能为空")
    @Pattern(regexp = "^20\\d{10}$", message = "学号必须为20开头的12位数字")
    private String studentId;

    private String phone;

    @NotBlank(message = "专业不能为空")
    @Size(max = 100, message = "专业长度不能超过100个字符")
    @Pattern(regexp = "^[\\u4e00-\\u9fff]{2,100}$", message = "专业必须为中文")
    private String major;

    private String selfIntro;

    private String skills;
}
