package top.hcode.hoj.service.admin.role.impl;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import top.hcode.hoj.common.result.CommonResult;
import top.hcode.hoj.dao.user.RoleAuthEntityService;
import top.hcode.hoj.dao.user.RoleEntityService;
import top.hcode.hoj.dao.user.UserRoleEntityService;
import top.hcode.hoj.mapper.AuthMapper;
import top.hcode.hoj.mapper.RoleAuthMapper;
import top.hcode.hoj.pojo.entity.user.Auth;
import top.hcode.hoj.pojo.entity.user.Role;
import top.hcode.hoj.pojo.entity.user.RoleAuth;
import top.hcode.hoj.pojo.entity.user.UserRole;
import top.hcode.hoj.pojo.vo.RoleAuthsVO;
import top.hcode.hoj.service.admin.role.AdminRoleService;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

/**
 * @Author: Open436
 * @Date: 2026/6/10
 * @Description: HOJ 角色权限管理 Service 实现
 */
@Service
@Slf4j(topic = "hoj")
public class AdminRoleServiceImpl implements AdminRoleService {

    // 系统内置角色 ID，不可删除
    private static final List<Long> SYSTEM_ROLE_IDS = Arrays.asList(1000L, 1001L, 1002L, 1003L, 1004L, 1005L, 1006L, 1007L, 1008L);

    @Autowired
    private RoleEntityService roleEntityService;

    @Autowired
    private RoleAuthEntityService roleAuthEntityService;

    @Autowired
    private UserRoleEntityService userRoleEntityService;

    @Autowired
    private RoleAuthMapper roleAuthMapper;

    @Autowired
    private AuthMapper authMapper;

    @Override
    public CommonResult<List<RoleAuthsVO>> getRoles() {
        List<Role> roles = roleEntityService.list();
        List<RoleAuthsVO> result = new ArrayList<>();
        for (Role role : roles) {
            RoleAuthsVO vo = roleAuthMapper.getRoleAuths(role.getId());
            if (vo == null) {
                vo = new RoleAuthsVO();
                vo.setId(role.getId());
                vo.setRole(role.getRole());
                vo.setDescription(role.getDescription());
                vo.setStatus(role.getStatus());
                vo.setGmtCreate(role.getGmtCreate());
                vo.setGmtModified(role.getGmtModified());
                vo.setAuths(new ArrayList<>());
            }
            result.add(vo);
        }
        return CommonResult.successResponse(result);
    }

    @Override
    public CommonResult<Void> createRole(Role role) {
        // 检查角色名是否已存在
        QueryWrapper<Role> queryWrapper = new QueryWrapper<>();
        queryWrapper.eq("role", role.getRole());
        if (roleEntityService.count(queryWrapper) > 0) {
            return CommonResult.errorResponse("角色名已存在");
        }
        role.setStatus(0);
        boolean success = roleEntityService.save(role);
        if (success) {
            return CommonResult.successResponse("创建成功");
        }
        return CommonResult.errorResponse("创建失败");
    }

    @Override
    public CommonResult<Void> updateRole(Role role) {
        if (role.getId() == null) {
            return CommonResult.errorResponse("角色ID不能为空");
        }
        // 检查是否为系统角色
        if (SYSTEM_ROLE_IDS.contains(role.getId())) {
            // 系统角色只允许修改描述，不允许修改角色名和状态
            Role existing = roleEntityService.getById(role.getId());
            if (existing == null) {
                return CommonResult.errorResponse("角色不存在");
            }
            existing.setDescription(role.getDescription());
            boolean success = roleEntityService.updateById(existing);
            return success ? CommonResult.successResponse("更新成功") : CommonResult.errorResponse("更新失败");
        }
        boolean success = roleEntityService.updateById(role);
        return success ? CommonResult.successResponse("更新成功") : CommonResult.errorResponse("更新失败");
    }

    @Override
    public CommonResult<Void> deleteRole(Long id) {
        if (SYSTEM_ROLE_IDS.contains(id)) {
            return CommonResult.errorResponse("系统内置角色不可删除");
        }
        // 删除角色关联的权限
        QueryWrapper<RoleAuth> authQuery = new QueryWrapper<>();
        authQuery.eq("role_id", id);
        roleAuthEntityService.remove(authQuery);
        // 删除用户-角色关联
        QueryWrapper<UserRole> userRoleQuery = new QueryWrapper<>();
        userRoleQuery.eq("role_id", id);
        userRoleEntityService.remove(userRoleQuery);
        // 删除角色
        boolean success = roleEntityService.removeById(id);
        return success ? CommonResult.successResponse("删除成功") : CommonResult.errorResponse("删除失败");
    }

    @Override
    public CommonResult<RoleAuthsVO> getRoleAuth(Long rid) {
        RoleAuthsVO vo = roleAuthMapper.getRoleAuths(rid);
        if (vo == null) {
            return CommonResult.errorResponse("角色不存在");
        }
        return CommonResult.successResponse(vo);
    }

    @Override
    public CommonResult<List<Auth>> getAllAuth() {
        List<Auth> auths = authMapper.selectList(null);
        return CommonResult.successResponse(auths);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public CommonResult<Void> changeRoleAuth(Long roleId, List<Integer> authIds) {
        // 删除原有权限关联
        QueryWrapper<RoleAuth> deleteQuery = new QueryWrapper<>();
        deleteQuery.eq("role_id", roleId);
        roleAuthEntityService.remove(deleteQuery);
        // 插入新的权限关联
        if (authIds != null && !authIds.isEmpty()) {
            List<RoleAuth> roleAuths = new ArrayList<>();
            for (Integer authId : authIds) {
                RoleAuth roleAuth = new RoleAuth();
                roleAuth.setRoleId(roleId);
                roleAuth.setAuthId(authId.longValue());
                roleAuths.add(roleAuth);
            }
            roleAuthEntityService.saveBatch(roleAuths);
        }
        return CommonResult.successResponse("权限更新成功");
    }

    @Override
    public CommonResult<Void> changeUserRole(String uid, Long roleId) {
        // 查找用户的现有角色
        QueryWrapper<UserRole> query = new QueryWrapper<>();
        query.eq("uid", uid);
        UserRole existing = userRoleEntityService.getOne(query);
        if (existing == null) {
            return CommonResult.errorResponse("用户角色记录不存在");
        }
        existing.setRoleId(roleId);
        boolean success = userRoleEntityService.updateById(existing);
        if (success) {
            // 清除 Shiro 授权缓存，下次访问时重新授权
            userRoleEntityService.deleteCache(uid, false);
            return CommonResult.successResponse("用户角色更新成功");
        }
        return CommonResult.errorResponse("用户角色更新失败");
    }
}
