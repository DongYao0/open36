package com.open436.auth.service;

import com.open436.auth.base.BaseApiTest;
import com.open436.auth.config.CacheConfig;
import com.open436.auth.repository.HomepageContentRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.mock.mockito.SpyBean;
import org.springframework.cache.Cache;
import org.springframework.cache.CacheManager;
import org.springframework.cache.interceptor.CacheErrorHandler;

import java.util.Map;

import static org.junit.jupiter.api.Assertions.assertDoesNotThrow;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.times;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

/**
 * 阶段3验收：首页公共内容 Redis 缓存行为。
 * 1. 连续请求只访问一次 Repository（缓存命中）；
 * 2. Service 直调两次只查一次库；
 * 3. 响应带公共 Cache-Control 头；
 * 4. Redis 故障时 errorHandler 吞异常（降级直查可用）；
 * 5. 空库仍返回 200。
 */
class HomepagePublicCacheTest extends BaseApiTest {

    @SpyBean
    private HomepageContentRepository repository;

    @Autowired
    private HomepagePublicService homepagePublicService;

    @Autowired
    private CacheManager cacheManager;

    @BeforeEach
    void cleanCacheBetweenTests() {
        Cache cache = cacheManager.getCache(CacheConfig.CACHE_HOMEPAGE_PUBLIC);
        if (cache != null) {
            cache.clear();
        }
    }

    @Test
    void consecutiveHttpReads_QueryRepositoryOnlyOnce() throws Exception {
        mockMvc.perform(get("/api/users/homepage/public"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(200));
        verify(repository, times(1)).findAll();

        mockMvc.perform(get("/api/users/homepage/public"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(200));
        // 两次 HTTP 读取后，findAll 仍只有 1 次 —— 第二次命中缓存
        verify(repository, times(1)).findAll();
    }

    @Test
    void serviceDirect_TwoCallsOneRepositoryHit() {
        Map<String, com.fasterxml.jackson.databind.JsonNode> first = homepagePublicService.loadPublicModules();
        Map<String, com.fasterxml.jackson.databind.JsonNode> second = homepagePublicService.loadPublicModules();
        verify(repository, times(1)).findAll();
        assertEquals(first.keySet(), second.keySet());
    }

    @Test
    void publicRead_ReturnsCacheControlHeader() throws Exception {
        mockMvc.perform(get("/api/users/homepage/public"))
                .andExpect(status().isOk())
                .andExpect(result -> {
                    String cc = result.getResponse().getHeader("Cache-Control");
                    assert cc != null && cc.contains("max-age=60") : "Cache-Control 缺失或不符: " + cc;
                });
    }

    @Test
    void cacheErrorHandler_SwallowsRedisFailures() {
        CacheErrorHandler handler = new CacheConfig().errorHandler();
        Cache mockCache = mock(Cache.class);
        when(mockCache.getName()).thenReturn("homepagePublic");
        RuntimeException boom = new RuntimeException("connection refused");

        assertDoesNotThrow(() -> handler.handleCacheGetError(boom, mockCache, "all"));
        assertDoesNotThrow(() -> handler.handleCachePutError(boom, mockCache, "all", new Object()));
        assertDoesNotThrow(() -> handler.handleCacheEvictError(boom, mockCache, "all"));
        assertDoesNotThrow(() -> handler.handleCacheClearError(boom, mockCache));
    }

    @Test
    void emptyModules_StillReturn200() throws Exception {
        // DB 无行时（或全被 reset），公共接口必须正常返回空对象
        mockMvc.perform(get("/api/users/homepage/public"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(200));
    }

    @Test
    void saveModule_EvictsPublicCache() throws Exception {
        mockMvc.perform(get("/api/users/homepage/public")).andExpect(status().isOk());
        verify(repository, times(1)).findAll();

        String token = loginAsAdmin();
        mockMvc.perform(org.springframework.test.web.servlet.request.MockMvcRequestBuilders
                        .put("/api/users/homepage/admin/about")
                        .header("token", token)
                        .contentType(org.springframework.http.MediaType.APPLICATION_JSON)
                        .content("{\"headText\":\"缓存驱逐验证\"}"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(200));

        // 保存后公共读必须重新查库（缓存已驱逐）
        mockMvc.perform(get("/api/users/homepage/public"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.data.about.headText").value("缓存驱逐验证"));
        verify(repository, times(2)).findAll();
    }

    @Test
    void resetModule_EvictsPublicCache() throws Exception {
        mockMvc.perform(get("/api/users/homepage/public")).andExpect(status().isOk());

        String token = loginAsAdmin();
        mockMvc.perform(org.springframework.test.web.servlet.request.MockMvcRequestBuilders
                        .post("/api/users/homepage/admin/about/reset")
                        .header("token", token))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(200));

        mockMvc.perform(get("/api/users/homepage/public")).andExpect(status().isOk());
        // 重置后公共读重新查库
        verify(repository, times(2)).findAll();
    }

    private String loginAsAdmin() throws Exception {
        com.open436.auth.dto.LoginRequest request = new com.open436.auth.dto.LoginRequest();
        request.setUsername("test_admin");
        request.setPassword("test123");
        String response = mockMvc.perform(org.springframework.test.web.servlet.request.MockMvcRequestBuilders
                        .post("/api/auth/login")
                        .contentType(org.springframework.http.MediaType.APPLICATION_JSON)
                        .content(toJson(request)))
                .andExpect(status().isOk())
                .andReturn().getResponse().getContentAsString();
        return objectMapper.readTree(response).get("data").get("token").asText();
    }
}
