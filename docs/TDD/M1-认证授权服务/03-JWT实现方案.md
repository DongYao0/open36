# M1 认证授权服务 - Sa-Token 自动续签实现方案

## 文档信息

**服务名称**: 认证授权服务 (auth-service)  
**认证框架**: Sa-Token 1.37.0  
**Token 方案**: 自动续签（单 Token + 自动续期）  
**版本**: v3.0  
**最新文档**: [登录流程设计.md](登录流程设计.md) (v4.0)

---

## 📌 方案概述

### 从双 Token 到自动续签

**双 Token 方案的问题**:

- ❌ 需要客户端手动管理两个 Token
- ❌ 需要实现 Refresh Token 的刷新逻辑
- ❌ 需要维护 Refresh Token 的黑名单
- ❌ 代码复杂度高

**自动续签方案的优势**:

- ✅ 只需一个 Token，简单易用
- ✅ Sa-Token 自动续签，无需手动刷新
- ✅ 用户在有效期内访问会自动延长有效期
- ✅ 代码量减少约 40%

---

## 目录

1. [Sa-Token 自动续签原理](#sa-token-自动续签原理)
2. [Token 生成与管理](#token-生成与管理)
3. [自动续签配置](#自动续签配置)
4. [登出机制](#登出机制)
5. [与 Kong Gateway 集成](#与-kong-gateway-集成)
6. [完整实现示例](#完整实现示例)

---

## Sa-Token 自动续签原理

### 1.1 工作原理

```
用户登录
  ↓
生成Token（有效期30天）
  ↓
用户访问API（在有效期内）
  ↓
Sa-Token自动检测Token即将过期
  ↓
自动延长Token有效期（+30天）
  ↓
用户无感知，继续使用
```

### 1.2 关键配置

```yaml
sa-token:
  # Token有效期30天
  timeout: 2592000

  # 自动续签配置
  auto-renew:
    # 开启自动续签
    enabled: true
    # 每次续签时续签30天
    timeout: 2592000
```

**工作原理**:

- 用户登录时生成 Token，有效期 30 天
- 当用户在有效期内访问 API 时，Sa-Token 会检测 Token 的剩余有效期
- 如果剩余有效期不足续签时间的一半，则自动延长 30 天
- 用户无需手动刷新，只要持续使用就会自动续期

### 1.3 Token 结构

**Token 格式**: UUID（如：`satoken:satoken:open436`）

**存储位置**: Redis

**Redis Key 格式**:

```
satoken:login:token:{tokenValue}
```

**Redis Value 内容**:

```json
{
  "id": "1",
  "loginId": "1",
  "role": "user",
  "username": "alice"
}
```

**TTL**: 自动续签会更新 TTL

---

## Token 生成与管理

### 2.1 用户登录

**文件**: `AuthService.java`

```java
package com.open436.auth.service;

import cn.dev33.satoken.stp.StpUtil;
import cn.dev33.satoken.stp.SaLoginModel;
import com.open436.auth.entity.UserAuth;
import com.open436.auth.repository.UserAuthRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class AuthService {

    private final UserAuthRepository userAuthRepository;
    private final PasswordEncoder passwordEncoder;

    /**
     * 用户登录
     */
    public LoginResponse login(LoginRequest request) {
        // 1. 查询用户
        UserAuth user = userAuthRepository
            .findByUsername(request.getUsername())
            .orElseThrow(() -> new BusinessException(40101001, "用户名或密码错误"));

        // 2. 检查账号状态
        if ("disabled".equals(user.getStatus())) {
            throw new BusinessException(40301001, "账号已被禁用，请联系管理员");
        }

        // 3. 验证密码
        if (!passwordEncoder.matches(request.getPassword(), user.getPasswordHash())) {
            throw new BusinessException(40101001, "用户名或密码错误");
        }

        // 4. 获取用户角色
        String role = user.getRoles().stream()
            .findFirst()
            .map(Role::getCode)
            .orElse("user");

        // 5. 使用Sa-Token登录（自动生成Token）
        StpUtil.login(user.getId(), new SaLoginModel()
            .setDevice("web")
            .setIsLastingCookie(true)  // 持久化cookie
            .setTimeout(2592000)        // 30天有效期
        );

        // 6. 设置Session信息（存储在Redis）
        StpUtil.getSession().set("username", user.getUsername());
        StpUtil.getSession().set("role", role);

        // 7. 获取Token值
        String token = StpUtil.getTokenValue();

        // 8. 更新最后登录时间
        user.setLastLoginAt(LocalDateTime.now());
        userAuthRepository.save(user);

        // 9. 返回结果
        return LoginResponse.builder()
            .token(token)
            .expiresIn(2592000)  // 30天
            .user(UserInfoResponse.from(user))
            .build();
    }
}
```

**Sa-Token 自动完成的工作**:

- ✅ 生成 UUID 格式的 Token
- ✅ 将用户信息存入 Redis Session
- ✅ 设置 Token 有效期
- ✅ 启用自动续签

### 2.2 获取当前用户

```java
/**
 * 获取当前登录用户
 */
public UserInfo getCurrentUser() {
    // 1. 检查是否登录
    if (!StpUtil.isLogin()) {
        throw new BusinessException(40101002, "未登录");
    }

    // 2. 获取用户ID
    Long userId = StpUtil.getLoginIdAsLong();

    // 3. 从Session获取用户名和角色
    String username = (String) StpUtil.getSession().get("username");
    String role = (String) StpUtil.getSession().get("role");

    return UserInfo.builder()
        .id(userId)
        .username(username)
        .role(role)
        .build();
}
```

---

## 自动续签配置

### 3.1 配置文件

**application.yml**:

```yaml
sa-token:
  # token 名称
  token-name: satoken

  # token 有效期（30天）
  timeout: 2592000

  # token 临时有效期（-1表示永久有效）
  active-timeout: -1

  # 是否允许同一账号并发登录
  is-concurrent: true

  # 在多人登录同一账号时，是否共用一个 token
  is-share: true

  # token 风格
  token-style: uuid

  # 是否输出操作日志
  is-log: false

  # 自动续签配置
  auto-renew:
    # 是否开启自动续签
    enabled: true
    # 每次续签时续签多久（30天）
    timeout: 2592000
```

### 3.2 自动续签工作原理

**续签时机**:

- 用户每次访问需要认证的接口时
- Sa-Token 会检查 Token 的剩余有效期
- 如果剩余有效期 < 续签时间的一半，则自动续签

**续签示例**:

```
初始Token：有效期30天（2592000秒）
5天后访问：剩余25天，大于15天，不续签
16天后访问：剩余14天，小于15天，自动续签至30天
```

### 3.3 自定义续签逻辑

```java
/**
 * 自定义Sa-Token配置
 */
@Configuration
public class SaTokenConfig {

    /**
     * 注册 Sa-Token 拦截器，打开注解式鉴权功能
     */
    @Bean
    public SaInterceptor getSaInterceptor() {
        return new SaInterceptor()
            .addInterceptor(new SaInterceptorImpl());
    }

    /**
     * 自定义拦截器，实现自动续签
     */
    public static class SaInterceptorImpl implements StpInterface {

        @Override
        public List<String> getPermissionList(Object loginId, String loginType) {
            // 返回该用户的所有权限
            return Collections.emptyList();
        }

        @Override
        public List<String> getRoleList(Object loginId, String loginType) {
            // 返回该用户的所有角色
            return Collections.emptyList();
        }
    }
}
```

---

## 登出机制

### 4.1 用户登出

```java
/**
 * 用户登出
 */
public void logout() {
    // Sa-Token登出（自动清除Session和Token）
    StpUtil.logout();
}
```

**Sa-Token 登出功能**:

- ✅ 清除 Redis 中的 Session 数据
- ✅ 清除 Token 缓存
- ✅ 标记 Token 为已失效
- ✅ 所有设备都被登出（如果是单点登录配置）

### 4.2 踢人下线

```java
/**
 * 踢出指定用户（管理员功能）
 */
public void kickout(Long userId) {
    // Sa-Token踢人下线
    StpUtil.kickout(userId);
}
```

**使用场景**:

- 管理员禁用用户账号
- 用户修改密码后踢出旧会话
- 检测到异常登录行为

---

## 与 Kong Gateway 集成

### 5.1 Kong 配置

**JWT 配置**:

```yaml
consumers:
  - username: open436-system
    custom_id: system
    jwt_secrets:
      - key: open436
        secret: ${JWT_SECRET}
        algorithm: HS256
```

**路由配置**:

```yaml
routes:
  - name: auth-route
    paths:
      - /api/auth
    service: auth-service
    plugins:
      - name: jwt
        config:
          key_names:
            - open436
```

### 5.2 后端获取用户信息

**从 Sa-Token 获取**:

```java
@RestController
@RequestMapping("/api/auth")
public class AuthController {

    @GetMapping("/current")
    public ResponseEntity<ApiResponse<UserInfo>> getCurrentUser() {
        // 从Sa-Token获取当前用户
        Long userId = StpUtil.getLoginIdAsLong();
        String username = (String) StpUtil.getSession().get("username");
        String role = (String) StpUtil.getSession().get("role");

        UserInfo userInfo = UserInfo.builder()
            .id(userId)
            .username(username)
            .role(role)
            .build();

        return ResponseEntity.ok(ApiResponse.success(userInfo));
    }
}
```

---

## 完整实现示例

### 6.1 登录 Controller

```java
@RestController
@RequestMapping("/api/auth")
@RequiredArgsConstructor
public class AuthController {

    private final AuthService authService;

    /**
     * 用户登录
     */
    @PostMapping("/login")
    public ResponseEntity<ApiResponse<LoginResponse>> login(
            @Valid @RequestBody LoginRequest request) {

        LoginResponse response = authService.login(request);

        return ResponseEntity.ok(
            ApiResponse.<LoginResponse>builder()
                .code(200)
                .message("登录成功")
                .data(response)
                .timestamp(System.currentTimeMillis())
                .build()
        );
    }

    /**
     * 用户登出
     */
    @PostMapping("/logout")
    @SaCheckLogin
    public ResponseEntity<ApiResponse<Void>> logout() {
        authService.logout();

        return ResponseEntity.ok(
            ApiResponse.<Void>builder()
                .code(200)
                .message("已成功退出登录")
                .timestamp(System.currentTimeMillis())
                .build()
        );
    }

    /**
     * 获取当前用户信息
     */
    @GetMapping("/current")
    @SaCheckLogin
    public ResponseEntity<ApiResponse<UserInfo>> getCurrentUser() {
        UserInfo userInfo = authService.getCurrentUser();

        return ResponseEntity.ok(
            ApiResponse.<UserInfo>builder()
                .code(200)
                .message("获取成功")
                .data(userInfo)
                .timestamp(System.currentTimeMillis())
                .build()
        );
    }
}
```

### 6.2 完整流程示例

**1. 用户登录**:

```bash
POST /api/auth/login
Content-Type: application/json

{
  "username": "alice",
  "password": "password123"
}

# 响应
{
  "code": 200,
  "message": "登录成功",
  "data": {
    "token": "satoken:satoken:xyz123...",
    "expiresIn": 2592000,
    "user": {
      "id": 1,
      "username": "alice",
      "role": "user"
    }
  }
}
```

**2. 使用 Token 访问 API**:

```bash
GET /api/auth/current
Authorization: Bearer satoken:satoken:xyz123...

# Sa-Token自动续签（无感知）
# Redis TTL自动延长30天

# 响应
{
  "code": 200,
  "data": {
    "id": 1,
    "username": "alice",
    "role": "user"
  }
}
```

**3. 用户登出**:

```bash
POST /api/auth/logout
Authorization: Bearer satoken:satoken:xyz123...

# Sa-Token清除Session和Token
# Redis中数据被删除

# 响应
{
  "code": 200,
  "message": "已成功退出登录"
}
```

---

## 优势总结

### 相比双 Token 方案

| 特性       | 双 Token 方案    | 自动续签方案 |
| ---------- | ---------------- | ------------ |
| Token 数量 | 2 个             | 1 个         |
| 手动刷新   | 需要             | 不需要       |
| 代码复杂度 | 高               | 低           |
| 用户体验   | 需要处理刷新逻辑 | 完全无感     |
| 安全性     | 高               | 高           |
| 代码量     | ~300 行          | ~150 行      |

### 自动续签方案特点

- ✅ **简单易用**: 只需一个 Token，客户端无需维护刷新逻辑
- ✅ **用户体验好**: 用户持续使用会自动续期，不会突然过期
- ✅ **代码量少**: 相比双 Token 方案减少约 40%代码
- ✅ **安全可靠**: Sa-Token 框架成熟稳定，自动续签机制可靠
- ✅ **配置灵活**: 可配置续签时间和触发条件

---

**文档版本**: v3.0  
**创建日期**: 2025-10-23  
**最后更新**: 2025-01-XX  
**维护者**: 后端开发团队

---

## 📝 变更日志

### v3.0 (2025-01-XX)

**重大变更**:

1. ✅ 从双 Token 方案改为自动续签方案
2. ✅ 移除 Refresh Token 相关逻辑
3. ✅ 简化登录和登出流程
4. ✅ 代码量减少约 40%

**新增内容**:

- Sa-Token 自动续签配置
- 自动续签工作原理说明
- 完整的实现示例

**删除内容**:

- Refresh Token 生成和管理
- Token 刷新接口
- Refresh Token 黑名单管理

### v2.0 (2025-10-27)

- 使用 Sa-Token 双 Token 方案
- 代码量相比 Spring Security 减少 64%

### v1.0 (2025-10-23)

- 初始版本
- 使用 Spring Security + JWT

---

**参考资料**:

- [Sa-Token 官方文档](https://sa-token.cc) ⭐
- [Sa-Token GitHub](https://github.com/dromara/sa-token)
- [Kong Gateway 文档](https://docs.konghq.com/)
