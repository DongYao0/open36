package com.open436.auth.controller;

import cn.dev33.satoken.annotation.SaCheckRole;
import cn.dev33.satoken.stp.StpUtil;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.open436.auth.dto.ApiResponse;
import com.open436.auth.entity.HomepageContent;
import com.open436.auth.enums.ErrorCode;
import com.open436.auth.exception.BusinessException;
import com.open436.auth.repository.HomepageContentRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.Map;
import java.util.Set;
import org.springframework.transaction.annotation.Transactional;

/**
 * 首页内容管理控制器（Landing 3D 首页后台化）
 * 前台匿名聚合读取 + 管理端按模块整存整取（content 为 JSON，排序=数组下标）
 */
@Slf4j
@RestController
@RequestMapping("/api/users/homepage")
@RequiredArgsConstructor
public class HomepageController {

    private final HomepageContentRepository repository;
    private final ObjectMapper objectMapper;

    /** 合法模块白名单 */
    private static final Set<String> MODULES = Set.of(
            "about", "experiences", "technologies", "works", "feedbacks");

    /**
     * 前台聚合读取（匿名）：返回全部模块，DB 无行的模块不返回该键（前台用默认值）
     * content 原样透传 JSON
     */
    @GetMapping("/public")
    public ResponseEntity<ApiResponse<Map<String, JsonNode>>> getPublic() {
        Map<String, JsonNode> result = new HashMap<>();
        for (HomepageContent row : repository.findAll()) {
            try {
                result.put(row.getModule(), objectMapper.readTree(row.getContent()));
            } catch (Exception e) {
                log.warn("homepage_content 模块 {} JSON 解析失败，跳过: {}", row.getModule(), e.getMessage());
            }
        }
        return ResponseEntity.ok(ApiResponse.<Map<String, JsonNode>>builder()
                .code(200).message("获取成功").data(result).build());
    }

    /**
     * 管理端读取单模块（admin）
     */
    @GetMapping("/admin/{module}")
    @SaCheckRole("admin")
    public ResponseEntity<ApiResponse<JsonNode>> getModule(@PathVariable String module) {
        checkModule(module);
        return repository.findByModule(module)
                .map(row -> {
                    try {
                        return ResponseEntity.ok(ApiResponse.<JsonNode>builder()
                                .code(200).message("获取成功")
                                .data(objectMapper.readTree(row.getContent())).build());
                    } catch (Exception e) {
                        return ResponseEntity.<ApiResponse<JsonNode>>ok(
                                ApiResponse.<JsonNode>builder()
                                        .code(500).message("内容 JSON 解析失败").data(null).build());
                    }
                })
                .orElseGet(() -> ResponseEntity.ok(ApiResponse.<JsonNode>builder()
                        .code(200).message("模块未配置，前台使用默认值").data(null).build()));
    }

    /**
     * 管理端全量保存单模块（admin，upsert，body 即 content JSON）
     */
    @PutMapping("/admin/{module}")
    @SaCheckRole("admin")
    public ResponseEntity<ApiResponse<Void>> saveModule(
            @PathVariable String module,
            @RequestBody JsonNode body) {
        checkModule(module);
        if (body == null || body.isNull() || body.isEmpty()) {
            return ResponseEntity.badRequest().body(ApiResponse.<Void>builder()
                    .code(400).message("内容不能为空").build());
        }
        HomepageContent row = repository.findByModule(module).orElse(new HomepageContent());
        row.setModule(module);
        row.setContent(body.toString());
        row.setUpdatedBy(Long.parseLong(StpUtil.getLoginId().toString()));
        row.setUpdatedAt(LocalDateTime.now());
        repository.save(row);
        log.info("首页模块 {} 已更新 by user {}", module, row.getUpdatedBy());
        return ResponseEntity.ok(ApiResponse.<Void>builder()
                .code(200).message("保存成功").build());
    }

    /**
     * 管理端重置单模块（admin，删行后前台回退默认内容）
     */
    @PostMapping("/admin/{module}/reset")
    @SaCheckRole("admin")
    @Transactional
    public ResponseEntity<ApiResponse<Void>> resetModule(@PathVariable String module) {
        checkModule(module);
        repository.deleteByModule(module);
        log.info("首页模块 {} 已重置为默认", module);
        return ResponseEntity.ok(ApiResponse.<Void>builder()
                .code(200).message("已重置，前台将使用默认内容").build());
    }

    private void checkModule(String module) {
        if (!MODULES.contains(module)) {
            throw new BusinessException(ErrorCode.INVALID_PARAMETER,
                    "非法模块: " + module + "，合法值: " + MODULES);
        }
    }
}
