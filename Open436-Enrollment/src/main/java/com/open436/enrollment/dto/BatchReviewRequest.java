package com.open436.enrollment.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotEmpty;
import lombok.Data;

import java.util.List;

@Data
public class BatchReviewRequest {

    @NotEmpty(message = "ID列表不能为空")
    private List<Long> ids;

    @NotBlank(message = "审核状态不能为空")
    private String status;

    private String reason;
}
