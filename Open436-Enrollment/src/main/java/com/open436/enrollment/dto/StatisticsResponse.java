package com.open436.enrollment.dto;

import lombok.Builder;
import lombok.Data;

@Data
@Builder
public class StatisticsResponse {

    private long total;
    private long pending;
    private long approved;
    private long rejected;
    private int approvalRate;
}
