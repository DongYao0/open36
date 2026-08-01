package com.open436.auth.dto;

import jakarta.validation.constraints.Size;
import lombok.Data;

/**
 * 更新用户资料请求
 */
@Data
public class UpdateProfileRequest {

    @Size(min = 2, max = 20, message = "昵称长度必须在2-20个字符之间")
    private String nickname;

    @Size(max = 200, message = "个人简介不能超过200个字符")
    private String bio;

    @Size(max = 500, message = "头像URL不能超过500个字符")
    private String avatarUrl;
}
