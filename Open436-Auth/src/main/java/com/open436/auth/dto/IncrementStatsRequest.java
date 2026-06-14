package com.open436.auth.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;
import lombok.Data;

/**
 * 统计递增请求
 */
@Data
public class IncrementStatsRequest {

    @NotBlank(message = "field 不能为空")
    @Pattern(regexp = "posts_count|replies_count|likes_received|favorites_received",
             message = "field 必须是 posts_count|replies_count|likes_received|favorites_received")
    private String field;

    private int value = 1;
}
