package com.open436.enrollment.repository;

import com.open436.enrollment.entity.AssignmentAllocation;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
public interface AssignmentAllocationRepository extends JpaRepository<AssignmentAllocation, Long> {

    /**
     * 查询某个作业的所有分配记录
     */
    List<AssignmentAllocation> findByAssignmentIdOrderByAssignedAtDesc(Long assignmentId);

    /**
     * 查询某个作业已分配的学生ID列表
     */
    @Query("SELECT aa.studentId FROM AssignmentAllocation aa WHERE aa.assignmentId = :assignmentId")
    List<Long> findStudentIdsByAssignmentId(@Param("assignmentId") Long assignmentId);

    /**
     * 检查某个学生是否已被分配某作业
     */
    boolean existsByAssignmentIdAndStudentId(Long assignmentId, Long studentId);

    /**
     * 查找特定分配记录
     */
    Optional<AssignmentAllocation> findByAssignmentIdAndStudentId(Long assignmentId, Long studentId);

    /**
     * 删除某个作业的所有分配
     */
    void deleteByAssignmentId(Long assignmentId);

    /**
     * 删除某个作业的特定学生分配
     */
    void deleteByAssignmentIdAndStudentId(Long assignmentId, Long studentId);

    /**
     * 统计某个作业的分配人数
     */
    long countByAssignmentId(Long assignmentId);
}
