package com.open436.enrollment.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotEmpty;
import lombok.Data;

import java.util.List;

@Data
public class BatchInterviewStatusRequest {

    @NotEmpty(message = "面试ID列表不能为空")
    private List<Long> ids;

    @NotBlank(message = "面试状态不能为空")
    private String status;
}
