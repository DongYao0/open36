package com.open436.auth.repository;

import com.open436.auth.entity.RegistrationRecord;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.Optional;

public interface RegistrationRecordRepository extends JpaRepository<RegistrationRecord, Long> {

    Optional<RegistrationRecord> findByIdempotencyKey(String idempotencyKey);

    Optional<RegistrationRecord> findByUserId(Long userId);

    /**
     * 按 idempotency key 取事务级咨询锁（PostgreSQL）。
     * 同 Key 并发注册在此排队：首个事务提交后，后到者能读到 SUCCEEDED
     * 记录并直接复用结果；避免"插入竞争→事务中止"的经典陷阱。
     * 返回值无意义，仅取锁副作用。
     */
    @Query(value = "SELECT pg_advisory_xact_lock(hashtext(:key))", nativeQuery = true)
    Object acquireAdvisoryLock(@Param("key") String key);
}
