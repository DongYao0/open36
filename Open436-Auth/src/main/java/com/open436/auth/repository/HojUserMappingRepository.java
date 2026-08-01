package com.open436.auth.repository;

import com.open436.auth.entity.HojUserMapping;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.Optional;

/**
 * HOJ 用户映射表 Repository
 */
@Repository
public interface HojUserMappingRepository extends JpaRepository<HojUserMapping, Long> {

    Optional<HojUserMapping> findByAuthUserId(Long authUserId);
}
