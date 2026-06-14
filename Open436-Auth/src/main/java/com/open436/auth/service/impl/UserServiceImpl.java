package com.open436.auth.service.impl;

import cn.dev33.satoken.stp.StpUtil;
import com.open436.auth.dto.CreateUserRequest;
import com.open436.auth.dto.UpdatePasswordRequest;
import com.open436.auth.dto.UserInfoResponse;
import com.open436.auth.entity.Role;
import com.open436.auth.entity.UserAuth;
import com.open436.auth.enums.ErrorCode;
import com.open436.auth.enums.UserStatus;
import com.open436.auth.exception.BusinessException;
import com.open436.auth.repository.RoleRepository;
import com.open436.auth.repository.UserAuthRepository;
import com.open436.auth.service.PermissionService;
import com.open436.auth.service.RoleService;
import com.open436.auth.service.UserService;
import com.open436.auth.service.UserProfileService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.stream.Collectors;

/**
 * 用户管理服务实现类
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class UserServiceImpl implements UserService {
    
    private final UserAuthRepository userAuthRepository;
    private final RoleRepository roleRepository;
    private final PasswordEncoder passwordEncoder;
    private final PermissionService permissionService;
    private final RoleService roleService;
    private final UserProfileService userProfileService;
    
    /**
     * 创建用户（管理员功能）
     */
    @Override
    @Transactional
    public UserInfoResponse createUser(CreateUserRequest request) {
        log.info("创建用户: username={}, role={}", request.getUsername(), request.getRole());
        
        // 1. 检查用户名是否已存在
        if (userAuthRepository.existsByUsername(request.getUsername())) {
            log.warn("创建用户失败: 用户名已存在 - {}", request.getUsername());
            throw new BusinessException(ErrorCode.USERNAME_EXISTS);
        }
        
        // 2. 查询角色
        Role role = roleRepository.findByCode(request.getRole())
            .orElseThrow(() -> new BusinessException(ErrorCode.ROLE_NOT_FOUND));
        
        // 3. 加密密码
        String passwordHash = passwordEncoder.encode(request.getPassword());

        // 4. 校验客户端权限值
        String clientPermission = request.getClientPermission();
        if (clientPermission == null || clientPermission.isBlank()) {
            clientPermission = "all";
        } else if (!java.util.Set.of("all", "forum", "quiz", "none").contains(clientPermission)) {
            throw new BusinessException(ErrorCode.INVALID_PARAMETER, "客户端权限值无效");
        }

        // 5. 创建用户
        UserAuth user = new UserAuth();
        user.setUsername(request.getUsername());
        user.setPasswordHash(passwordHash);
        user.setStatus(request.getStatus());
        user.setStudentId(request.getStudentId());
        user.setRealName(request.getRealName());
        user.setPhone(request.getPhone());
        user.setMajor(request.getMajor());
        user.setClientPermission(clientPermission);
        user.getRoles().add(role);
        
        user = userAuthRepository.save(user);

        // 6. 创建用户资料和统计
        userProfileService.createProfileForUser(user.getId(), "用户" + user.getId());

        log.info("用户创建成功: userId={}, username={}, role={}",
                 user.getId(), user.getUsername(), request.getRole());

        // 7. 返回用户信息
        return UserInfoResponse.builder()
            .id(user.getId())
            .username(user.getUsername())
            .role(request.getRole())
            .status(user.getStatus())
            .build();
    }
    
    /**
     * 获取用户列表（管理员功能）
     */
    @Override
    @Transactional(readOnly = true)
    public List<UserInfoResponse> getUserList(String status) {
        List<UserAuth> users;
        if (status != null && !status.isEmpty()) {
            users = userAuthRepository.findByStatus(status);
        } else {
            users = userAuthRepository.findAll();
        }
        // 在事务内完成映射，避免 LazyInitializationException
        List<UserInfoResponse> result = new java.util.ArrayList<>();
        for (UserAuth u : users) {
            result.add(UserInfoResponse.builder()
                .id(u.getId())
                .username(u.getUsername())
                .role(u.getPrimaryRoleCode())
                .status(u.getStatus())
                .studentId(u.getStudentId())
                .realName(u.getRealName())
                .phone(u.getPhone())
                .major(u.getMajor())
                .clientPermission(u.getClientPermission())
                .build());
        }
        return result;
    }

    /**
     * 根据ID查询用户
     */
    @Override
    @Transactional(readOnly = true)
    public UserInfoResponse getUserById(Long userId) {
        UserAuth user = userAuthRepository.findById(userId)
            .orElseThrow(() -> new BusinessException(ErrorCode.USER_NOT_FOUND));
        return UserInfoResponse.builder()
            .id(user.getId())
            .username(user.getUsername())
            .role(user.getPrimaryRoleCode())
            .status(user.getStatus())
            .studentId(user.getStudentId())
            .realName(user.getRealName())
            .phone(user.getPhone())
            .major(user.getMajor())
            .clientPermission(user.getClientPermission())
            .build();
    }

    /**
     * 批量查询用户信息
     */
    @Override
    @Transactional(readOnly = true)
    public List<UserInfoResponse> getUsersByIds(List<Long> userIds) {
        if (userIds == null || userIds.isEmpty()) {
            return List.of();
        }
        List<UserAuth> users = userAuthRepository.findAllById(userIds);
        return users.stream().map(u -> UserInfoResponse.builder()
            .id(u.getId())
            .username(u.getUsername())
            .role(u.getPrimaryRoleCode())
            .status(u.getStatus())
            .studentId(u.getStudentId())
            .realName(u.getRealName())
            .phone(u.getPhone())
            .major(u.getMajor())
            .clientPermission(u.getClientPermission())
            .build()
        ).toList();
    }

    /**
     * 启用/禁用/审核用户（管理员功能）
     */
    @Override
    @Transactional
    public UserInfoResponse updateUserStatus(Long userId, String status) {
        log.info("更新用户状态: userId={}, status={}", userId, status);
        
        // 1. 查询用户
        UserAuth user = userAuthRepository.findById(userId)
            .orElseThrow(() -> new BusinessException(ErrorCode.USER_NOT_FOUND));
        
        // 2. 更新状态
        user.setStatus(status);
        userAuthRepository.save(user);
        
        // 3. 清除用户权限和角色缓存
        permissionService.clearUserPermissionsCache(userId);
        roleService.clearUserRolesCache(userId);
        
        // 4. 如果是禁用或待审核操作，踢出该用户（强制重新登录）
        if (UserStatus.DISABLED.getCode().equals(status) || UserStatus.PENDING.getCode().equals(status)) {
            StpUtil.kickout(userId);
            log.info("用户已被踢出: userId={}", userId);
        }
        
        log.info("用户状态更新成功: userId={}, status={}", userId, status);

        // 5. 返回用户信息
        String role = user.getPrimaryRoleCode();
        
        return UserInfoResponse.builder()
            .id(user.getId())
            .username(user.getUsername())
            .role(role)
            .status(user.getStatus())
            .build();
    }
    
    /**
     * 修改密码（用户自己）
     */
    @Override
    @Transactional
    public void updatePassword(UpdatePasswordRequest request) {
        // 1. 获取当前用户ID
        Long userId = StpUtil.getLoginIdAsLong();
        log.info("修改密码: userId={}", userId);
        
        // 2. 校验两次新密码是否一致
        if (!request.getNewPassword().equals(request.getConfirmPassword())) {
            throw new BusinessException(ErrorCode.PASSWORD_MISMATCH);
        }

        // 3. 查询用户
        UserAuth user = userAuthRepository.findById(userId)
            .orElseThrow(() -> new BusinessException(ErrorCode.USER_NOT_FOUND));

        // 4. 验证原密码
        if (!passwordEncoder.matches(request.getOldPassword(), user.getPasswordHash())) {
            log.warn("修改密码失败: 原密码错误 - userId={}", userId);
            throw new BusinessException(ErrorCode.WRONG_OLD_PASSWORD);
        }
        
        // 5. 验证新密码不能与原密码相同
        if (passwordEncoder.matches(request.getNewPassword(), user.getPasswordHash())) {
            throw new BusinessException(ErrorCode.PASSWORD_SAME_AS_OLD);
        }
        
        // 5. 加密新密码并更新
        String newPasswordHash = passwordEncoder.encode(request.getNewPassword());
        user.setPasswordHash(newPasswordHash);
        userAuthRepository.save(user);
        
        // 6. 清除所有 Token（强制重新登录）
        StpUtil.kickout(userId);
        
        log.info("密码修改成功: userId={}", userId);
    }
    
    /**
     * 重置用户密码（管理员功能）
     */
    @Override
    @Transactional
    public void resetPassword(Long userId, String newPassword) {
        log.info("重置用户密码: userId={}", userId);
        
        // 1. 查询用户
        UserAuth user = userAuthRepository.findById(userId)
            .orElseThrow(() -> new BusinessException(ErrorCode.USER_NOT_FOUND));
        
        // 2. 加密新密码并更新
        String newPasswordHash = passwordEncoder.encode(newPassword);
        user.setPasswordHash(newPasswordHash);
        userAuthRepository.save(user);
        
        // 3. 清除该用户的所有 Token
        StpUtil.kickout(userId);
        
        log.info("密码重置成功: userId={}", userId);
    }

    /**
     * 获取用户状态
     */
    @Override
    @Transactional(readOnly = true)
    public String getUserStatus(Long userId) {
        UserAuth user = userAuthRepository.findById(userId)
            .orElseThrow(() -> new BusinessException(ErrorCode.USER_NOT_FOUND));
        return user.getStatus();
    }

    /**
     * 删除用户（管理员功能）
     */
    @Override
    @Transactional
    public void deleteUser(Long userId) {
        log.info("删除用户: userId={}", userId);

        // 1. 检查用户是否存在（避免 LAZY 集合加载问题，使用 deleteById）
        if (!userAuthRepository.existsById(userId)) {
            throw new BusinessException(ErrorCode.USER_NOT_FOUND);
        }

        // 2. 清除用户权限和角色缓存
        permissionService.clearUserPermissionsCache(userId);
        roleService.clearUserRolesCache(userId);

        // 3. 踢出该用户（强制重新登录）
        StpUtil.kickout(userId);

        // 4. 删除用户（数据库外键已配置 ON DELETE CASCADE，自动清理 user_roles）
        userAuthRepository.deleteById(userId);

        log.info("用户删除成功: userId={}", userId);
    }

    /**
     * 批量删除用户（管理员功能）
     */
    @Override
    @Transactional
    public void deleteUsers(List<Long> userIds) {
        log.info("批量删除用户: count={}", userIds.size());
        for (Long userId : userIds) {
            deleteUser(userId);
        }
        log.info("批量删除用户完成: count={}", userIds.size());
    }

    /**
     * 更新用户客户端权限（管理员功能）
     */
    @Override
    @Transactional
    public UserInfoResponse updateUserPermission(Long userId, String clientPermission) {
        log.info("更新用户客户端权限: userId={}, clientPermission={}", userId, clientPermission);

        // 1. 查询用户
        UserAuth user = userAuthRepository.findById(userId)
            .orElseThrow(() -> new BusinessException(ErrorCode.USER_NOT_FOUND));

        // 2. 更新权限
        user.setClientPermission(clientPermission);
        userAuthRepository.save(user);

        // 3. 清除缓存
        permissionService.clearUserPermissionsCache(userId);

        log.info("用户客户端权限更新成功: userId={}, clientPermission={}", userId, clientPermission);

        String role = user.getPrimaryRoleCode();
        return UserInfoResponse.builder()
            .id(user.getId())
            .username(user.getUsername())
            .role(role)
            .status(user.getStatus())
            .clientPermission(user.getClientPermission())
            .build();
    }

    /**
     * 更新用户角色（管理员功能）
     */
    @Override
    @Transactional
    public UserInfoResponse updateUserRole(Long userId, String role) {
        log.info("更新用户角色: userId={}, role={}", userId, role);

        // 1. 查询用户
        UserAuth user = userAuthRepository.findById(userId)
            .orElseThrow(() -> new BusinessException(ErrorCode.USER_NOT_FOUND));

        // 2. 查找目标角色实体
        Role targetRole = roleRepository.findByCode(role)
            .orElseThrow(() -> new BusinessException(ErrorCode.ROLE_NOT_FOUND));

        // 3. 清除现有角色，添加新角色
        user.getRoles().clear();
        user.getRoles().add(targetRole);

        // 4. 根据角色设置客户端权限
        String clientPermission;
        switch (role) {
            case "admin":
                clientPermission = "all";
                break;
            case "user":
                clientPermission = "all";
                break;
            case "viewer":
                clientPermission = "forum";
                break;
            default:
                clientPermission = "forum";
        }
        user.setClientPermission(clientPermission);

        userAuthRepository.save(user);

        // 5. 清除缓存
        permissionService.clearUserPermissionsCache(userId);

        log.info("用户角色更新成功: userId={}, role={}", userId, role);

        return UserInfoResponse.builder()
            .id(user.getId())
            .username(user.getUsername())
            .role(role)
            .status(user.getStatus())
            .clientPermission(user.getClientPermission())
            .build();
    }

    /**
     * 批量更新用户状态（管理员功能）
     */
    @Override
    @Transactional
    public void batchUpdateStatus(List<Long> userIds, String status) {
        log.info("批量更新用户状态: count={}, status={}", userIds.size(), status);

        for (Long userId : userIds) {
            updateUserStatus(userId, status);
        }

        log.info("批量更新用户状态完成: count={}", userIds.size());
    }
}


