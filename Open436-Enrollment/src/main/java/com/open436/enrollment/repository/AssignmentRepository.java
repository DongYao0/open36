package com.open436.enrollment.repository;

import com.open436.enrollment.entity.Assignment;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.time.LocalDateTime;
import java.util.List;

@Repository
public interface AssignmentRepository extends JpaRepository<Assignment, Long> {

    /**
     * 分页查询作业列表
     */
    Page<Assignment> findAllByOrderByCreatedAtDesc(Pageable pageable);

    /**
     * 按状态查询作业
     */
    Page<Assignment> findByStatusOrderByCreatedAtDesc(String status, Pageable pageable);

    /**
     * 查询进行中的作业
     */
    List<Assignment> findByStatusAndDeadlineAfter(String status, LocalDateTime now);

    /**
     * 查询已过期但状态仍为active的作业
     */
    @Query("SELECT a FROM Assignment a WHERE a.status = 'active' AND a.deadline < :now")
    List<Assignment> findExpiredActiveAssignments(@Param("now") LocalDateTime now);
}
