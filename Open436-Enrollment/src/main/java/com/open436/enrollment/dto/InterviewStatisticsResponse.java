package com.open436.enrollment.dto;

import lombok.Builder;
import lombok.Data;

@Data
@Builder
public class InterviewStatisticsResponse {

    private long total;
    private long pending;
    private long passed;
    private long failed;
    private int passRate;
}
