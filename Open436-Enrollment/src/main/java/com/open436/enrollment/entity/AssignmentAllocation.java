package com.open436.enrollment.entity;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.hibernate.annotations.CreationTimestamp;

import java.time.LocalDateTime;

/**
 * 作业分配实体 - 记录作业分配给哪些学生
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@Entity
@Table(name = "assignment_allocations", uniqueConstraints = {
    @UniqueConstraint(columnNames = {"assignment_id", "student_id"})
})
public class AssignmentAllocation {

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
     * 学生姓名（冗余字段，方便查询）
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

    @CreationTimestamp
    @Column(name = "assigned_at", updatable = false)
    private LocalDateTime assignedAt;
}
