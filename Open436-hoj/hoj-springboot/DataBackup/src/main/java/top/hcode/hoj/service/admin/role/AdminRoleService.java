package top.hcode.hoj.service.admin.role;

import top.hcode.hoj.common.result.CommonResult;
import top.hcode.hoj.pojo.entity.user.Auth;
import top.hcode.hoj.pojo.entity.user.Role;
import top.hcode.hoj.pojo.vo.RoleAuthsVO;

import java.util.List;

/**
 * @Author: Open436
 * @Date: 2026/6/10
 * @Description: HOJ 角色权限管理 Service 接口
 */
public interface AdminRoleService {

    CommonResult<List<RoleAuthsVO>> getRoles();

    CommonResult<Void> createRole(Role role);

    CommonResult<Void> updateRole(Role role);

    CommonResult<Void> deleteRole(Long id);

    CommonResult<RoleAuthsVO> getRoleAuth(Long rid);

    CommonResult<List<Auth>> getAllAuth();

    CommonResult<Void> changeRoleAuth(Long roleId, List<Integer> authIds);

    CommonResult<Void> changeUserRole(String uid, Long roleId);
}
