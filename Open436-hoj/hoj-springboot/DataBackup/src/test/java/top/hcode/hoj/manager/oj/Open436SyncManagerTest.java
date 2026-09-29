package top.hcode.hoj.manager.oj;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.test.util.ReflectionTestUtils;
import top.hcode.hoj.common.exception.StatusFailException;
import top.hcode.hoj.dao.user.UserInfoEntityService;
import top.hcode.hoj.dao.user.UserRecordEntityService;
import top.hcode.hoj.dao.user.UserRoleEntityService;
import top.hcode.hoj.pojo.dto.Open436SyncDTO;
import top.hcode.hoj.pojo.entity.user.UserInfo;
import top.hcode.hoj.pojo.vo.UserInfoVO;
import top.hcode.hoj.utils.JwtUtils;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
class Open436SyncManagerTest {

    @InjectMocks
    private Open436SyncManager manager;
    @Mock
    private JwtUtils jwtUtils;
    @Mock
    private UserInfoEntityService userInfoEntityService;
    @Mock
    private UserRoleEntityService userRoleEntityService;
    @Mock
    private UserRecordEntityService userRecordEntityService;

    @BeforeEach
    void setUp() {
        ReflectionTestUtils.setField(manager, "apiKey", "test-key");
    }

    @Test
    void mappedUidKeepsAdminRenamedAccount() throws Exception {
        UserInfo renamed = new UserInfo().setUuid("uid-1").setUsername("T").setNickname("田涛");
        when(userInfoEntityService.getById("uid-1")).thenReturn(renamed);

        UserInfoVO result = manager.sync(request("田涛", "uid-1"));

        assertEquals("uid-1", result.getUid());
        assertEquals("T", result.getUsername());
        verify(userInfoEntityService, never()).getOne(any(QueryWrapper.class), eq(false));
        verify(userInfoEntityService, never()).save(any(UserInfo.class));
    }

    @Test
    void missingMappedUidFailsWithoutCreatingOrRebinding() {
        when(userInfoEntityService.getById("missing-uid")).thenReturn(null);

        StatusFailException error = assertThrows(StatusFailException.class,
                () -> manager.sync(request("田涛", "missing-uid")));

        assertEquals("已绑定的 HOJ 账户不存在，请联系管理员修复账户映射", error.getMessage());
        verify(userInfoEntityService, never()).getOne(any(QueryWrapper.class), eq(false));
        verify(userInfoEntityService, never()).save(any(UserInfo.class));
    }

    private Open436SyncDTO request(String username, String hojUid) {
        Open436SyncDTO dto = new Open436SyncDTO();
        dto.setUsername(username);
        dto.setHojUid(hojUid);
        dto.setNickname("田涛");
        dto.setRole("user");
        dto.setApiKey("test-key");
        return dto;
    }
}
