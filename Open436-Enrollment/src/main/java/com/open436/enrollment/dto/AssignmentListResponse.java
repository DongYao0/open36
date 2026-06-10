package com.open436.enrollment.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;
import java.util.List;

/**
 * 作业列表响应
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class AssignmentListResponse {

    private List<AssignmentItem> list;
    private Long total;

    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class AssignmentItem {
        private Long id;
        private String title;
        private String description;
        private LocalDateTime deadline;
        private String status;
        private Long assignedCount;  // 已分配人数
        private Long submittedCount; // 已提交人数（作业收集用）
        private Long totalCount;     // 总人数（作业收集用）
        private LocalDateTime createdAt;
    }
}
