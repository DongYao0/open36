package com.open436.auth.repository;

import com.open436.auth.entity.UserStatistics;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

@Repository
public interface UserStatisticsRepository extends JpaRepository<UserStatistics, Long> {

    @Modifying
    @Query("UPDATE UserStatistics s SET s.postsCount = s.postsCount + :delta WHERE s.userId = :userId")
    int incrementPostsCount(@Param("userId") Long userId, @Param("delta") int delta);

    @Modifying
    @Query("UPDATE UserStatistics s SET s.repliesCount = s.repliesCount + :delta WHERE s.userId = :userId")
    int incrementRepliesCount(@Param("userId") Long userId, @Param("delta") int delta);

    @Modifying
    @Query("UPDATE UserStatistics s SET s.likesReceived = s.likesReceived + :delta WHERE s.userId = :userId")
    int incrementLikesReceived(@Param("userId") Long userId, @Param("delta") int delta);

    @Modifying
    @Query("UPDATE UserStatistics s SET s.favoritesReceived = s.favoritesReceived + :delta WHERE s.userId = :userId")
    int incrementFavoritesReceived(@Param("userId") Long userId, @Param("delta") int delta);
}
