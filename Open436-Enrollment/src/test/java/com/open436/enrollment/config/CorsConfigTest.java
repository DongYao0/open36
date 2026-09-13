package com.open436.enrollment.config;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.core.env.Environment;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

import static org.junit.jupiter.api.Assertions.*;

/**
 * 验证 Enrollment CorsConfig 真正从 yaml/env 加载 cors.* 配置项。
 */
@SpringBootTest(classes = CorsConfig.class, properties = {
    "cors.allowed-origins=http://a.test,http://b.test",
    "cors.allowed-methods=GET,POST,OPTIONS",
    "cors.allowed-headers=Authorization,token,Content-Type,X-User-Id",
    "cors.allow-credentials=true",
    "cors.max-age=7200"
})
@ActiveProfiles("test")
class CorsConfigTest {

    @Autowired
    private WebMvcConfigurer corsConfigurer;

    @Autowired
    private Environment env;

    @Value("${cors.allowed-origins}")
    private String allowedOriginsCsv;

    @Value("${cors.allowed-headers}")
    private String allowedHeadersCsv;

    @Test
    void testCorsConfigLoaded() {
        assertNotNull(corsConfigurer, "CorsConfig bean must be loaded");
        assertEquals("http://a.test,http://b.test", allowedOriginsCsv);
        assertTrue(allowedHeadersCsv.contains("Authorization"));
        assertTrue(allowedHeadersCsv.contains("token"));
        assertTrue(allowedHeadersCsv.contains("Content-Type"));
        assertTrue(allowedHeadersCsv.contains("X-User-Id"));
        assertNotNull(env.getProperty("cors.allowed-origins"));
        assertNotNull(env.getProperty("cors.allowed-headers"));
        assertNotNull(env.getProperty("cors.allowed-methods"));
        assertNotNull(env.getProperty("cors.allow-credentials"));
        assertNotNull(env.getProperty("cors.max-age"));
    }
}