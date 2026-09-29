package top.hcode.hoj.manager.oj;

import cn.hutool.core.util.IdUtil;
import cn.hutool.crypto.SecureUtil;
import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;
import top.hcode.hoj.common.exception.StatusFailException;
import top.hcode.hoj.dao.user.UserInfoEntityService;
import top.hcode.hoj.dao.user.UserRecordEntityService;
import top.hcode.hoj.dao.user.UserRoleEntityService;
import top.hcode.hoj.pojo.dto.Open436SyncDTO;
import top.hcode.hoj.pojo.entity.user.UserInfo;
import top.hcode.hoj.pojo.entity.user.UserRecord;
import top.hcode.hoj.pojo.entity.user.UserRole;
import top.hcode.hoj.pojo.vo.UserInfoVO;
import top.hcode.hoj.utils.JwtUtils;

/**
 * Open436 用户同步到 HOJ
 */
@Component
public class Open436SyncManager {

    @Value("${hoj.open436.api-key:default-key-change-me}")
    private String apiKey;

    @Autowired
    private JwtUtils jwtUtils;

    @Autowired
    private UserInfoEntityService userInfoEntityService;

    @Autowired
    private UserRoleEntityService userRoleEntityService;

    @Autowired
    private UserRecordEntityService userRecordEntityService;

    @Transactional(rollbackFor = Exception.class)
    public UserInfoVO sync(Open436SyncDTO dto) throws StatusFailException {
        if (!apiKey.equals(dto.getApiKey())) {
            throw new StatusFailException("API Key 验证失败");
        }

        String username = dto.getUsername().trim();
        String mappedUid = dto.getHojUid() == null ? null : dto.getHojUid().trim();
        UserInfo userInfo = null;
        if (mappedUid != null && !mappedUid.isEmpty()) {
            userInfo = userInfoEntityService.getById(mappedUid);
            if (userInfo == null) {
                throw new StatusFailException("已绑定的 HOJ 账户不存在，请联系管理员修复账户映射");
            }
        } else {
            QueryWrapper<UserInfo> usernameQuery = new QueryWrapper<>();
            usernameQuery.eq("username", username);
            userInfo = userInfoEntityService.getOne(usernameQuery, false);
        }

        // 映射 Open436 角色到 HOJ 角色：admin->1000(超级管理员), 其他->1002(普通用户)
        Long roleId = "admin".equals(dto.getRole()) ? 1000L : 1002L;

        String uid;
        if (userInfo == null) {
            uid = IdUtil.simpleUUID();

            UserInfo newUser = new UserInfo();
            newUser.setUuid(uid);
            newUser.setUsername(username);
            newUser.setPassword(SecureUtil.md5(IdUtil.simpleUUID()));
            newUser.setNickname(dto.getNickname());
            newUser.setAvatar(dto.getAvatar());
            newUser.setStatus(0);
            userInfoEntityService.save(newUser);
            userInfo = newUser;

            userRoleEntityService.save(new UserRole().setRoleId(roleId).setUid(uid));
            userRecordEntityService.save(new UserRecord().setUid(uid));
        } else {
            uid = userInfo.getUuid();
            boolean needUpdate = false;
            if (dto.getNickname() != null && !dto.getNickname().equals(userInfo.getNickname())) {
                userInfo.setNickname(dto.getNickname());
                needUpdate = true;
            }
            if (dto.getAvatar() != null && !dto.getAvatar().equals(userInfo.getAvatar())) {
                userInfo.setAvatar(dto.getAvatar());
                needUpdate = true;
            }
            if (needUpdate) {
                userInfoEntityService.updateById(userInfo);
            }
            // 同步角色变更
            QueryWrapper<UserRole> roleQuery = new QueryWrapper<>();
            roleQuery.eq("uid", uid);
            UserRole currentRole = userRoleEntityService.getOne(roleQuery, false);
            if (currentRole != null && !roleId.equals(currentRole.getRoleId())) {
                currentRole.setRoleId(roleId);
                userRoleEntityService.updateById(currentRole);
            }
        }

        String jwt = jwtUtils.generateToken(uid);

        UserInfoVO vo = new UserInfoVO();
        vo.setUid(uid);
        vo.setUsername(userInfo.getUsername());
        vo.setNickname(userInfo.getNickname());
        vo.setAvatar(userInfo.getAvatar());
        return vo;
    }
}
