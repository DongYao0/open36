package com.open436.auth.service.impl;

import cn.dev33.satoken.stp.StpUtil;
import com.open436.auth.dto.AlgoSyncRequest;
import com.open436.auth.dto.ApiResponse;
import com.open436.auth.entity.HojUserMapping;
import com.open436.auth.enums.TokenConstants;
import com.open436.auth.repository.HojUserMappingRepository;
import com.open436.auth.service.AlgoSyncService;
import com.open436.auth.service.RoleService;
import com.open436.auth.service.UserService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.*;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * 算法系统同步服务实现
 */
@Slf4j
@Service
public class AlgoSyncServiceImpl implements AlgoSyncService {

    @Value("${hoj.sync.url:http://localhost:8088}")
    private String hojSyncUrl;

    @Value("${hoj.sync.api-key:default-key-change-me}")
    private String hojApiKey;

    @Autowired
    private RoleService roleService;

    @Autowired
    private UserService userService;

    @Autowired
    private HojUserMappingRepository hojUserMappingRepository;

    private final RestTemplate restTemplate = new RestTemplate();

    @Override
    public ApiResponse<String> syncToHoj(AlgoSyncRequest request) {
        Long userId = StpUtil.getLoginIdAsLong();
        String username = (String) StpUtil.getSession().get(TokenConstants.SESSION_KEY_USERNAME);

        log.info("同步用户到 HOJ: userId={}, username={}", userId, username);

        // 校验用户状态，仅 active 用户可同步到 HOJ
        String status = userService.getUserStatus(userId);
        if (!"active".equals(status)) {
            log.warn("HOJ 同步被拒绝: 用户状态非 active, userId={}, status={}", userId, status);
            return ApiResponse.error(403, "用户未通过审核，无法访问算法平台");
        }

        // 查询用户角色
        List<String> roles = roleService.getUserRoleCodes(userId);
        String role = roles.isEmpty() ? TokenConstants.DEFAULT_ROLE : roles.get(0);

        return doSyncToHoj(userId, username, request != null ? request.getNickname() : null, role);
    }

    @Override
    public ApiResponse<String> syncUserToHoj(String username, String nickname, String role) {
        log.info("后台同步用户到 HOJ: username={}", username);
        return doSyncToHoj(null, username, nickname, role);
    }

    @Override
    public ApiResponse<String> syncUserToHoj(Long authUserId, String username, String nickname, String role) {
        log.info("后台同步用户到 HOJ: authUserId={}, username={}", authUserId, username);
        return doSyncToHoj(authUserId, username, nickname, role);
    }

    private ApiResponse<String> doSyncToHoj(Long authUserId, String username, String nickname, String role) {
        Map<String, Object> body = new HashMap<>();
        body.put("username", username);
        body.put("nickname", nickname);
        body.put("avatar", null);
        body.put("apiKey", hojApiKey);
        body.put("role", role);
        String mappedHojUid = null;
        if (authUserId != null) {
            mappedHojUid = hojUserMappingRepository.findByAuthUserId(authUserId)
                    .map(HojUserMapping::getHojUuid)
                    .orElse(null);
            if (mappedHojUid != null) {
                body.put("hojUid", mappedHojUid);
            }
        }

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);

        HttpEntity<Map<String, Object>> entity = new HttpEntity<>(body, headers);

        try {
            ResponseEntity<Map> response = restTemplate.exchange(
                    hojSyncUrl + "/api/open436-sync",
                    HttpMethod.POST,
                    entity,
                    Map.class
            );

            String hojToken = response.getHeaders().getFirst("Authorization");
            if (hojToken == null) {
                log.warn("HOJ 同步响应中未找到 Authorization Header");
                return ApiResponse.error(500, "HOJ 同步失败：未返回 Token");
            }

            // HOJ uid 是跨系统的不可变身份；用户名/昵称只用于展示。
            if (authUserId != null) {
                if (response.getBody() == null) {
                    throw new IllegalStateException("HOJ 同步响应缺少用户数据");
                }
                extractAndSaveHojMapping(authUserId, mappedHojUid, response.getBody());
            }

            log.info("HOJ 同步成功: username={}, authUserId={}", username, authUserId);
            return ApiResponse.success("同步成功", hojToken);
        } catch (Exception e) {
            log.error("HOJ 同步异常: username={}, authUserId={}, error={}", username, authUserId, e.getMessage(), e);
            return ApiResponse.error(500, "HOJ 同步失败：" + e.getMessage());
        }
    }

    /**
     * 从 HOJ 响应中提取 uid 并保存映射
     */
    @SuppressWarnings("unchecked")
    private void extractAndSaveHojMapping(Long authUserId, String mappedHojUid,
                                          Map<String, Object> responseBody) {
        Object data = responseBody.get("data");
        if (!(data instanceof Map)) {
            throw new IllegalStateException("HOJ 同步响应缺少用户数据");
        }
        Object uid = ((Map<String, Object>) data).get("uid");
        if (uid == null || uid.toString().trim().isEmpty()) {
            throw new IllegalStateException("HOJ 同步响应缺少 uid");
        }
        String hojUuid = uid.toString();
        if (mappedHojUid != null && !mappedHojUid.equals(hojUuid)) {
            throw new IllegalStateException("HOJ 返回 uid 与已绑定账户不一致");
        }
        HojUserMapping mapping = new HojUserMapping();
        mapping.setAuthUserId(authUserId);
        mapping.setHojUuid(hojUuid);
        hojUserMappingRepository.save(mapping);
        log.info("HOJ 映射保存成功: authUserId={}, hojUuid={}", authUserId, hojUuid);
    }
}
