package top.hcode.hoj.manager.admin.user;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.core.conditions.update.UpdateWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.test.util.ReflectionTestUtils;
import org.springframework.data.redis.core.RedisTemplate;
import top.hcode.hoj.common.exception.StatusFailException;
import top.hcode.hoj.dao.user.UserAcproblemEntityService;
import top.hcode.hoj.dao.user.UserInfoEntityService;
import top.hcode.hoj.dao.user.UserRoleEntityService;
import top.hcode.hoj.pojo.vo.UserRolesVO;
import top.hcode.hoj.utils.RedisUtils;

import java.util.Arrays;
import java.util.Collections;

import static org.junit.jupiter.api.Assertions.assertDoesNotThrow;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.lenient;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
class AdminUserManagerTest {

    @InjectMocks
    private AdminUserManager manager;
    @Mock
    private UserRoleEntityService userRoleEntityService;
    @Mock
    private UserInfoEntityService userInfoEntityService;
    @Mock
    private UserAcproblemEntityService userAcproblemEntityService;
    @BeforeEach
    void setUp() {
        RedisTemplate<String, Object> redisTemplate = mock(RedisTemplate.class);
        lenient().when(redisTemplate.keys(any())).thenReturn(Collections.emptySet());
        RedisUtils redisUtils = new RedisUtils();
        redisUtils.setRedisTemplate(redisTemplate);
        ReflectionTestUtils.setField(manager, "redisUtils", redisUtils);
    }

    @Test
    void creationRangeIsNormalizedAndOrderIsWhitelisted() {
        IPage<UserRolesVO> page = mock(IPage.class);
        when(userRoleEntityService.getUserList(10, 1, "田涛", false,
                1000L, 2000L, "desc")).thenReturn(page);

        manager.getUserList(10, 1, false, " 田涛 ", 2000L, 1000L, "drop table");

        verify(userRoleEntityService).getUserList(10, 1, "田涛", false,
                1000L, 2000L, "desc");
    }

    @Test
    void resetSolvedIsIdempotentButRejectsEmptySelection() throws Exception {
        assertDoesNotThrow(() -> manager.resetSolved(Arrays.asList("u1", "u1", " ")));
        verify(userAcproblemEntityService).remove(any(QueryWrapper.class));
        assertThrows(StatusFailException.class, () -> manager.resetSolved(Collections.emptyList()));
    }

    @Test
    void hiddenStateIsUpdatedForSelectedUsers() throws Exception {
        when(userInfoEntityService.update(any(UpdateWrapper.class))).thenReturn(true);
        manager.setHidden(Arrays.asList("u1", "u2"), true);

        verify(userInfoEntityService).update(any(UpdateWrapper.class));
        assertThrows(StatusFailException.class, () -> manager.setHidden(Arrays.asList("u1"), null));
    }
}
