package com.open436.enrollment.repository;

import com.open436.enrollment.entity.Interview;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
public interface InterviewRepository extends JpaRepository<Interview, Long> {

    List<Interview> findByEnrollmentIdOrderByRoundAsc(Long enrollmentId);

    Optional<Interview> findByEnrollmentIdAndRound(Long enrollmentId, Integer round);

    List<Interview> findByStatus(String status);

    List<Interview> findByAuthUserIdOrderByCreatedAtDesc(Long authUserId);

    long countByStatus(String status);

    boolean existsByEnrollmentId(Long enrollmentId);
}
