package com.open436.enrollment.dto;

import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotNull;
import lombok.Data;

import java.time.LocalDateTime;

@Data
public class InterviewRecordRequest {

    @NotNull(message = "报名申请ID不能为空")
    private Long enrollmentId;

    private Integer round;

    private LocalDateTime interviewDate;

    private String interviewer;

    @Min(value = 0, message = "评分最低0分")
    @Max(value = 10, message = "评分最高10分")
    private Integer score;

    private String summary;

    private String strengths;

    private String weaknesses;

    private String direction;
}
