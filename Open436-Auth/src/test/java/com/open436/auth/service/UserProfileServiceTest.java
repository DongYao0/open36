package com.open436.auth.service;

import com.open436.auth.dto.UserProfileResponse;
import com.open436.auth.entity.UserAuth;
import com.open436.auth.entity.UserProfile;
import com.open436.auth.file.FileServiceClient;
import com.open436.auth.repository.UserAuthRepository;
import com.open436.auth.repository.UserProfileRepository;
import com.open436.auth.repository.UserStatisticsRepository;
import com.open436.auth.service.impl.UserProfileServiceImpl;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.util.List;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
class UserProfileServiceTest {

    @Mock UserProfileRepository profileRepository;
    @Mock UserStatisticsRepository statisticsRepository;
    @Mock UserAuthRepository userAuthRepository;
    @Mock FileServiceClient fileServiceClient;
    @InjectMocks UserProfileServiceImpl service;

    @Test
    void batchProfilesUsesRealNameAndKeepsUsersWithoutProfile() {
        UserAuth first = new UserAuth();
        first.setId(1L);
        first.setRealName("张三");
        UserAuth second = new UserAuth();
        second.setId(2L);
        second.setRealName("李四");
        UserProfile profile = new UserProfile();
        profile.setUserId(1L);
        profile.setNickname("旧昵称");
        profile.setAvatarUrl("/objects/avatar.jpg");

        when(userAuthRepository.findAllById(List.of(1L, 2L))).thenReturn(List.of(first, second));
        when(profileRepository.findByUserIdIn(List.of(1L, 2L))).thenReturn(List.of(profile));

        List<UserProfileResponse> result = service.batchGetProfiles(List.of(1L, 2L));

        assertEquals(2, result.size());
        assertEquals("张三", result.get(0).getRealName());
        assertEquals("旧昵称", result.get(0).getNickname());
        assertEquals("李四", result.get(1).getNickname());
        assertNull(result.get(1).getAvatarUrl());
    }
}
