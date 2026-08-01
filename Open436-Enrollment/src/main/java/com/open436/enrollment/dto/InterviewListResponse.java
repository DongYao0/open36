package com.open436.enrollment.dto;

import lombok.Builder;
import lombok.Data;

import java.time.LocalDateTime;
import java.util.List;

@Data
@Builder
public class InterviewListResponse {

    private Long id;
    private Long enrollmentId;
    private Long authUserId;
    private String username;
    private String realName;
    private String studentId;
    private String phone;
    private String major;
    private String selfIntro;
    private String skills;
    private String status;
    private Integer round;
    private LocalDateTime interviewDate;
    private String interviewer;
    private Integer score;
    private String summary;
    private String strengths;
    private String weaknesses;
    private String direction;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;

    /** 该候选人所有面试轮次记录（详情页使用） */
    private List<InterviewRoundItem> rounds;

    @Data
    @Builder
    public static class InterviewRoundItem {
        private Long id;
        private Integer round;
        private String status;
        private LocalDateTime interviewDate;
        private String interviewer;
        private Integer score;
        private String summary;
        private String strengths;
        private String weaknesses;
        private String direction;
        private LocalDateTime createdAt;
    }
}
