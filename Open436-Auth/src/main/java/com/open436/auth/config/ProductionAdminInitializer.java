package com.open436.auth.config;

import com.open436.auth.entity.Role;
import com.open436.auth.entity.UserAuth;
import com.open436.auth.repository.RoleRepository;
import com.open436.auth.repository.UserAuthRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.ApplicationArguments;
import org.springframework.boot.ApplicationRunner;
import org.springframework.context.annotation.Profile;
import org.springframework.core.annotation.Order;
import org.springframework.security.crypto.bcrypt.BCrypt;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

import java.util.Locale;
import java.util.Optional;
import java.util.regex.Pattern;

/**
 * 生产环境管理员账号初始化器（仅在 spring.profiles.active=prod 下生效）。
 *
 * 流程（严格顺序）：
 *  1) 校验 ADMIN_BOOTSTRAP_USER / ADMIN_BOOTSTRAP_PASSWORD_HASH 必填且合法
 *  2) 校验 bootstrap 用户名不是 "admin" / "test"（V2/V10 默认账号，重名易混淆）
 *  3) 校验 password_hash 看起来像 BCrypt（2a/2b/2y 开头的 60 字符）
 *  4) 如目标用户名已存在：刷新密码哈希、状态、admin 角色
 *  5) 不存在则新建管理员
 *  6) 最后清理 V2/V10 残留的 admin / test 默认账号
 *  7) 终态校验：默认账号必须不存在
 *
 * 失败任意一步抛 IllegalStateException（Spring Boot 默认会让进程 exit 1）。
 */
@Component
@Profile("prod")
@Order(0)
public class ProductionAdminInitializer implements ApplicationRunner {

    private static final Logger log = LoggerFactory.getLogger(ProductionAdminInitializer.class);

    private static final String[] DEFAULT_USERNAMES_TO_REMOVE = {"admin", "test"};
    private static final Pattern BCRYPT_COST_10 = Pattern.compile(
            "^\\$2[aby]\\$10\\$[./A-Za-z0-9]{53}$");

    private final UserAuthRepository userRepo;
    private final RoleRepository roleRepo;

    @Value("${admin.bootstrap.user:${ADMIN_BOOTSTRAP_USER:}}")
    private String bootstrapUser;

    @Value("${admin.bootstrap.password-hash:${ADMIN_BOOTSTRAP_PASSWORD_HASH:}}")
    private String bootstrapPasswordHash;

    public ProductionAdminInitializer(UserAuthRepository userRepo,
                                      RoleRepository roleRepo) {
        this.userRepo = userRepo;
        this.roleRepo = roleRepo;
    }

    @Override
    @Transactional
    public void run(ApplicationArguments args) {
        log.info("[prod-init] === 生产环境管理员账号初始化 ===");

        // ── 1) 必填校验 ──
        if (isBlank(bootstrapUser) || isBlank(bootstrapPasswordHash)) {
            throw new IllegalStateException(
                "ADMIN_BOOTSTRAP_USER 与 ADMIN_BOOTSTRAP_PASSWORD_HASH 必须通过生产 .env 设置；"
                + "绝对不得留空、绝对不得使用弱默认。");
        }

        // ── 2) bootstrap 用户名必须不是默认账号名（避免歧义）──
        String lower = bootstrapUser.toLowerCase(Locale.ROOT).trim();
        for (String reserved : DEFAULT_USERNAMES_TO_REMOVE) {
            if (lower.equals(reserved)) {
                throw new IllegalStateException(
                    "ADMIN_BOOTSTRAP_USER 不能使用 Flyway 默认账号名 '" + reserved
                    + "'；生产请使用业务相关用户名（如 open436_root / ops 等）。");
            }
        }

        // ── 3) BCrypt 格式校验：必须是 Spring Security 接受的 BCrypt 哈希 ──
        //   Spring 不会让你把明文哈希当哈希用，所以这里直接用 PasswordEncoder.matches
        //   一个长度为 21 的已知字符串：返回 true 才是合法 BCrypt。
        if (!isValidBcryptHash(bootstrapPasswordHash)) {
            throw new IllegalStateException(
                "ADMIN_BOOTSTRAP_PASSWORD_HASH 不是合法 BCrypt 哈希（应为 $2a$10$... 或 $2b$10$...）。"
                + "请用 htpasswd -bnBC 10 \"\" \"YourPass\" | tr -d ':\\n' 生成，"
                + "并用单引号包裹写入 .env（避免 $ 被 shell 解释）。");
        }

        // ── 4) 刷新 / 创建管理员 ──
        Role adminRole = roleRepo.findByCode("admin")
                .orElseThrow(() -> new IllegalStateException(
                    "admin 角色不存在；Flyway 尚未初始化？"));

        Optional<UserAuth> existing = userRepo.findByUsername(bootstrapUser);
        if (existing.isPresent()) {
            UserAuth u = existing.get();
            u.setPasswordHash(bootstrapPasswordHash);
            u.setStatus("active");
            u.setClientPermission("all");
            u.getRoles().clear();
            u.getRoles().add(adminRole);
            userRepo.save(u);
            log.info("[prod-init] 已刷新生产管理员: {}", bootstrapUser);
        } else {
            UserAuth u = new UserAuth();
            u.setUsername(bootstrapUser);
            u.setPasswordHash(bootstrapPasswordHash);
            u.setStatus("active");
            u.setClientPermission("all");
            u.getRoles().add(adminRole);
            userRepo.save(u);
            log.info("[prod-init] 已创建生产管理员: {}", bootstrapUser);
        }

        // ── 6) 清理 V2/V10 默认账号（必须在创建 bootstrap 之后做，避免重名校验误伤）──
        for (String username : DEFAULT_USERNAMES_TO_REMOVE) {
            if (userRepo.existsByUsername(username)) {
                userRepo.deleteByUsername(username);
                log.warn("[prod-init] 已清理 Flyway 默认账号: {}", username);
            }
        }

        // ── 7) 终态校验 ──
        for (String u : DEFAULT_USERNAMES_TO_REMOVE) {
            if (userRepo.existsByUsername(u)) {
                throw new IllegalStateException("默认账号 " + u + " 仍在数据库中，初始化失败");
            }
        }
        if (!userRepo.existsByUsername(bootstrapUser)) {
            throw new IllegalStateException("bootstrap 管理员创建失败");
        }
        log.info("[prod-init] === 生产环境管理员账号初始化完成 ===");
    }

    private static boolean isBlank(String s) {
        return s == null || s.isBlank();
    }

    static boolean isValidBcryptHash(String candidate) {
        if (candidate == null || !BCRYPT_COST_10.matcher(candidate).matches()) {
            return false;
        }
        try {
            BCrypt.checkpw("open436-validation-probe", candidate);
            return true;
        } catch (IllegalArgumentException ex) {
            return false;
        }
    }
}
