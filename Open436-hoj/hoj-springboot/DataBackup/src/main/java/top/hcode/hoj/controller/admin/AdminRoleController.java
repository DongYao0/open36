package top.hcode.hoj.controller.admin;

import org.apache.shiro.authz.annotation.RequiresAuthentication;
import org.apache.shiro.authz.annotation.RequiresPermissions;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;
import top.hcode.hoj.common.result.CommonResult;
import top.hcode.hoj.pojo.entity.user.Auth;
import top.hcode.hoj.pojo.entity.user.Role;
import top.hcode.hoj.pojo.vo.RoleAuthsVO;
import top.hcode.hoj.service.admin.role.AdminRoleService;

import java.util.List;
import java.util.Map;

/**
 * @Author: Open436
 * @Date: 2026/6/10
 * @Description: HOJ 角色权限管理接口
 */
@RestController
@RequestMapping("/api/admin/role")
public class AdminRoleController {

    @Autowired
    private AdminRoleService adminRoleService;

    @GetMapping("/get-roles")
    @RequiresAuthentication
    @RequiresPermissions("user_admin")
    public CommonResult<List<RoleAuthsVO>> getRoles() {
        return adminRoleService.getRoles();
    }

    @PostMapping("")
    @RequiresAuthentication
    @RequiresPermissions("user_admin")
    public CommonResult<Void> createRole(@RequestBody Role role) {
        return adminRoleService.createRole(role);
    }

    @PutMapping("")
    @RequiresAuthentication
    @RequiresPermissions("user_admin")
    public CommonResult<Void> updateRole(@RequestBody Role role) {
        return adminRoleService.updateRole(role);
    }

    @DeleteMapping("")
    @RequiresAuthentication
    @RequiresPermissions("user_admin")
    public CommonResult<Void> deleteRole(@RequestBody Map<String, Object> params) {
        Long id = Long.valueOf(params.get("id").toString());
        return adminRoleService.deleteRole(id);
    }

    @GetMapping("/get-role-auth")
    @RequiresAuthentication
    @RequiresPermissions("user_admin")
    public CommonResult<RoleAuthsVO> getRoleAuth(@RequestParam(value = "rid") Long rid) {
        return adminRoleService.getRoleAuth(rid);
    }

    @GetMapping("/get-all-auth")
    @RequiresAuthentication
    @RequiresPermissions("user_admin")
    public CommonResult<List<Auth>> getAllAuth() {
        return adminRoleService.getAllAuth();
    }

    @PutMapping("/change-role-auth")
    @RequiresAuthentication
    @RequiresPermissions("user_admin")
    public CommonResult<Void> changeRoleAuth(@RequestBody Map<String, Object> params) {
        Long roleId = Long.valueOf(params.get("roleId").toString());
        @SuppressWarnings("unchecked")
        List<Integer> authIds = (List<Integer>) params.get("authIds");
        return adminRoleService.changeRoleAuth(roleId, authIds);
    }

    @PutMapping("/change-user-role")
    @RequiresAuthentication
    @RequiresPermissions("user_admin")
    public CommonResult<Void> changeUserRole(@RequestBody Map<String, Object> params) {
        String uid = (String) params.get("uid");
        Long roleId = Long.valueOf(params.get("roleId").toString());
        return adminRoleService.changeUserRole(uid, roleId);
    }
}
