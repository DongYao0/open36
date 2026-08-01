package com.open436.enrollment.entity;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.hibernate.annotations.CreationTimestamp;
import org.hibernate.annotations.UpdateTimestamp;

import java.time.LocalDateTime;

/**
 * 作业提交实体 - 记录学生的作业提交内容
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@Entity
@Table(name = "assignment_submissions", uniqueConstraints = {
    @UniqueConstraint(columnNames = {"assignment_id", "student_id"})
})
public class AssignmentSubmission {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    /**
     * 作业ID
     */
    @Column(name = "assignment_id", nullable = false)
    private Long assignmentId;

    /**
     * 学生ID
     */
    @Column(name = "student_id", nullable = false)
    private Long studentId;

    /**
     * 学生姓名（冗余字段）
     */
    @Column(name = "student_name", length = 50)
    private String studentName;

    /**
     * 学号
     */
    @Column(name = "student_no", length = 30)
    private String studentNo;

    /**
     * 专业
     */
    @Column(name = "major", length = 100)
    private String major;

    /**
     * 方向
     */
    @Column(name = "direction", length = 50)
    private String direction;

    /**
     * 提交状态：submitted-已提交，unsubmitted-未提交
     */
    @Column(nullable = false, length = 20)
    @Builder.Default
    private String status = "unsubmitted";

    /**
     * 提交的文字内容
     */
    @Column(columnDefinition = "TEXT")
    private String content;

    /**
     * 提交的文件路径（JSON数组格式）
     */
    @Column(name = "file_paths", columnDefinition = "TEXT")
    private String filePaths;

    /**
     * 提交时间
     */
    @Column(name = "submitted_at")
    private LocalDateTime submittedAt;

    @CreationTimestamp
    @Column(name = "created_at", updatable = false)
    private LocalDateTime createdAt;

    @UpdateTimestamp
    @Column(name = "updated_at")
    private LocalDateTime updatedAt;
}
