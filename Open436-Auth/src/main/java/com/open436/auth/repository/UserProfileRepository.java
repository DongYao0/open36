package com.open436.auth.repository;

import com.open436.auth.entity.UserProfile;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface UserProfileRepository extends JpaRepository<UserProfile, Long> {
    List<UserProfile> findByNicknameContainingIgnoreCase(String nickname);
    List<UserProfile> findByUserIdIn(List<Long> userIds);
}
