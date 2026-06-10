package com.open436.enrollment.repository;

import com.open436.enrollment.entity.AssignmentSubmission;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
public interface AssignmentSubmissionRepository extends JpaRepository<AssignmentSubmission, Long> {

    /**
     * 查询某个作业的所有提交记录
     */
    List<AssignmentSubmission> findByAssignmentIdOrderBySubmittedAtDesc(Long assignmentId);

    /**
     * 按状态查询某个作业的提交
     */
    List<AssignmentSubmission> findByAssignmentIdAndStatusOrderBySubmittedAtDesc(Long assignmentId, String status);

    /**
     * 查找特定学生的提交
     */
    Optional<AssignmentSubmission> findByAssignmentIdAndStudentId(Long assignmentId, Long studentId);

    /**
     * 检查学生是否已有提交记录
     */
    boolean existsByAssignmentIdAndStudentId(Long assignmentId, Long studentId);

    /**
     * 检查学生是否已提交
     */
    boolean existsByAssignmentIdAndStudentIdAndStatus(Long assignmentId, Long studentId, String status);

    /**
     * 统计某个作业的已提交人数
     */
    long countByAssignmentIdAndStatus(Long assignmentId, String status);
}
