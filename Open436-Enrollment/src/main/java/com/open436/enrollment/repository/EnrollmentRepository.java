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

    Optional<EnrollmentApplication> findByIdempotencyKey(String idempotencyKey);

    Optional<EnrollmentApplication> findFirstByRequestFingerprintAndProcessingStatus(
            String requestFingerprint, String processingStatus);

    /** 对账用：中间状态滞留超过阈值的报名（CREATING_USER/USER_CREATED 等） */
    @org.springframework.data.jpa.repository.Query("""
            SELECT a FROM EnrollmentApplication a
             WHERE a.processingStatus IN ('RECEIVED', 'CREATING_USER', 'USER_CREATED')
               AND a.submittedAt < :threshold
            """)
    java.util.List<EnrollmentApplication> findStuckIntermediate(
            @org.springframework.data.repository.query.Param("threshold") java.time.LocalDateTime threshold);

    List<EnrollmentApplication> findByProcessingStatus(String processingStatus);

    Page<EnrollmentApplication> findByProcessingStatus(String processingStatus, Pageable pageable);

    long countByProcessingStatus(String processingStatus);

    @org.springframework.data.jpa.repository.Query("""
            SELECT a FROM EnrollmentApplication a
             WHERE a.status = :status AND a.processingStatus = 'PENDING'
            """)
    List<EnrollmentApplication> findByStatus(
            @org.springframework.data.repository.query.Param("status") String status);

    @org.springframework.data.jpa.repository.Query("""
            SELECT a FROM EnrollmentApplication a
             WHERE a.status = :status AND a.processingStatus = 'PENDING'
            """)
    Page<EnrollmentApplication> findByStatus(
            @org.springframework.data.repository.query.Param("status") String status,
            Pageable pageable);

    @org.springframework.data.jpa.repository.Query("""
            SELECT COUNT(a) FROM EnrollmentApplication a
             WHERE a.status = :status AND a.processingStatus = 'PENDING'
            """)
    long countByStatus(
            @org.springframework.data.repository.query.Param("status") String status);
}
