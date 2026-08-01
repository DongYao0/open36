package com.open436.auth.dto;

import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import lombok.Data;

import java.util.List;

/**
 * 批量查询用户请求
 */
@Data
public class BatchUserRequest {

    @NotNull(message = "userIds 不能为空")
    @Size(max = 100, message = "单次最多查询100条")
    private List<Long> userIds;
}
