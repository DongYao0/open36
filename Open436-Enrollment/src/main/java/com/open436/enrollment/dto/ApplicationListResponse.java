package com.open436.enrollment.dto;

import lombok.Builder;
import lombok.Data;

import java.time.LocalDateTime;

@Data
@Builder
public class ApplicationListResponse {

    private Long id;
    private Long authUserId;
    private String username;
    private String realName;
    private String studentId;
    private String phone;
    private String major;
    private String selfIntro;
    private String skills;
    private String status;
    private LocalDateTime submittedAt;
    private LocalDateTime reviewedAt;
    private String reviewedBy;
    private String reviewReason;
}
