package com.open436.auth.repository;

import com.open436.auth.entity.HomepageContent;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.Optional;

@Repository
public interface HomepageContentRepository extends JpaRepository<HomepageContent, Long> {

    Optional<HomepageContent> findByModule(String module);

    void deleteByModule(String module);
}
