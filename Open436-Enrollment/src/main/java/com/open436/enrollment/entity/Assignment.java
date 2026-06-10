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
 * 作业实体
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@Entity
@Table(name = "assignments")
public class Assignment {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    /**
     * 作业标题
     */
    @Column(nullable = false, length = 200)
    private String title;

    /**
     * 作业描述
     */
    @Column(columnDefinition = "TEXT")
    private String description;

    /**
     * 截止时间
     */
    @Column(name = "deadline", nullable = false)
    private LocalDateTime deadline;

    /**
     * 状态：active-进行中，ended-已截止，pending-待分发
     */
    @Column(nullable = false, length = 20)
    @Builder.Default
    private String status = "pending";

    /**
     * 创建者ID
     */
    @Column(name = "creator_id")
    private Long creatorId;

    @CreationTimestamp
    @Column(name = "created_at", updatable = false)
    private LocalDateTime createdAt;

    @UpdateTimestamp
    @Column(name = "updated_at")
    private LocalDateTime updatedAt;
}
