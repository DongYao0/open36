package com.open436.enrollment.repository;

import com.open436.enrollment.entity.EnrollmentApplication;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
public interface EnrollmentRepository extends JpaRepository<EnrollmentApplication, Long> {

    boolean existsByAuthUserId(Long authUserId);

    Optional<EnrollmentApplication> findByAuthUserId(Long authUserId);

    List<EnrollmentApplication> findByStatus(String status);

    Page<EnrollmentApplication> findByStatus(String status, Pageable pageable);

    long countByStatus(String status);
}
