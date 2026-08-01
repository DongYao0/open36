package com.open436.auth.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotEmpty;
import jakarta.validation.constraints.Pattern;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;

/**
 * 批量更新用户状态请求 DTO
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class BatchUpdateStatusRequest {

    /**
     * 用户ID列表
     */
    @NotEmpty(message = "用户ID列表不能为空")
    private List<Long> ids;

    /**
     * 状态：active-已通过，rejected-未通过，pending-待审核
     */
    @NotBlank(message = "状态不能为空")
    @Pattern(regexp = "^(active|rejected|pending)$", message = "状态值无效")
    private String status;
}
