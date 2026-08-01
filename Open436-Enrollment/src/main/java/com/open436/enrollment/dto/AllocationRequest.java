package com.open436.enrollment.dto;

import jakarta.validation.constraints.NotEmpty;
import lombok.Data;

import java.util.List;

/**
 * 批量分配/移除请求
 */
@Data
public class AllocationRequest {

    @NotEmpty(message = "学生ID列表不能为空")
    private List<Long> studentIds;
}
