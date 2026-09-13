package com.open436.auth.service;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.open436.auth.config.CacheConfig;
import com.open436.auth.entity.HomepageContent;
import com.open436.auth.repository.HomepageContentRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.stereotype.Service;

import java.util.HashMap;
import java.util.Map;

/**
 * 首页公共内容读取服务（阶段3）
 *
 * 单独成 Bean 的原因：@Cacheable 基于 Spring AOP 代理，
 * 若与 Controller 同类自调用会绕过缓存切面。
 *
 * 1000 人在线场景下该接口是首页每次打开的必经请求，
 * 用 Redis 缓存挡住 repository.findAll()+逐行 JSON 解析；
 * Redis 故障由 CacheConfig.errorHandler() 降级为直查 DB。
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class HomepagePublicService {

    private final HomepageContentRepository repository;
    private final ObjectMapper objectMapper;

    /**
     * 聚合读取全部模块（匿名可调用）。
     * 独立 Bean 方法 + @Cacheable 代理生效；缓存 TTL 见 CacheConfig。
     */
    @Cacheable(cacheNames = CacheConfig.CACHE_HOMEPAGE_PUBLIC, key = "'all'")
    public Map<String, JsonNode> loadPublicModules() {
        Map<String, JsonNode> result = new HashMap<>();
        for (HomepageContent row : repository.findAll()) {
            try {
                result.put(row.getModule(), objectMapper.readTree(row.getContent()));
            } catch (Exception e) {
                log.warn("homepage_content 模块 {} JSON 解析失败，跳过: {}", row.getModule(), e.getMessage());
            }
        }
        return result;
    }
}
