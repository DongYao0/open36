package com.open436.auth.service;

import com.open436.auth.dto.CreateUserRequest;
import com.open436.auth.dto.UpdatePasswordRequest;
import com.open436.auth.dto.UserInfoResponse;

import java.util.List;

/**
 * 用户管理服务接口
 */
public interface UserService {

    /**
     * 创建用户（管理员功能）
     * @param request 创建用户请求
     * @return 用户信息
     */
    UserInfoResponse createUser(CreateUserRequest request);

    /**
     * 获取用户列表（管理员功能）
     * @param status 状态筛选（可选，null 则返回全部）
     * @return 用户列表
     */
    List<UserInfoResponse> getUserList(String status);

    /**
     * 根据ID查询用户
     * @param userId 用户ID
     * @return 用户信息
     */
    UserInfoResponse getUserById(Long userId);

    /**
     * 批量查询用户信息
     * @param userIds 用户ID列表
     * @return 用户列表
     */
    List<UserInfoResponse> getUsersByIds(List<Long> userIds);

    /**
     * 启用/禁用/审核用户（管理员功能）
     * @param userId 用户ID
     * @param status 新状态（pending/active/disabled）
     * @return 用户信息
     */
    UserInfoResponse updateUserStatus(Long userId, String status);

    /**
     * 修改密码（用户自己）
     * @param request 修改密码请求
     */
    void updatePassword(UpdatePasswordRequest request);

    /**
     * 重置用户密码（管理员功能）
     * @param userId 用户ID
     * @param newPassword 新密码
     */
    void resetPassword(Long userId, String newPassword);

    /**
     * 获取用户状态
     * @param userId 用户ID
     * @return 用户状态（pending/active/disabled）
     */
    String getUserStatus(Long userId);

    /**
     * 删除用户（管理员功能）
     * @param userId 用户ID
     */
    void deleteUser(Long userId);

    /**
     * 批量删除用户（管理员功能）
     * @param userIds 用户ID列表
     */
    void deleteUsers(java.util.List<Long> userIds);

    /**
     * 更新用户客户端权限（管理员功能）
     * @param userId 用户ID
     * @param clientPermission 客户端权限（all/forum/quiz/none）
     * @return 用户信息
     */
    UserInfoResponse updateUserPermission(Long userId, String clientPermission);

    /**
     * 更新用户角色（管理员功能）
     * @param userId 用户ID
     * @param role 角色（admin/user/viewer）
     * @return 用户信息
     */
    UserInfoResponse updateUserRole(Long userId, String role);

    /**
     * 批量更新用户状态（管理员功能）
     * @param userIds 用户ID列表
     * @param status 新状态
     */
    void batchUpdateStatus(List<Long> userIds, String status);
}


