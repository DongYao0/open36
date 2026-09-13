package com.open436.enrollment.config;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.util.StringUtils;
import org.springframework.web.servlet.config.annotation.CorsRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

import java.util.Arrays;
import java.util.List;

/**
 * CORS 配置 —— 真正读取 yaml `cors.*` 字段（逗号分隔）。
 * 任何修改必须同步 application.yml（dev profile）或通过环境变量覆盖（prod profile）。
 *
 * 默认 allowed-headers 包含业务实际使用的：Authorization、token（Sa-Token）、
 * Content-Type、X-User-*（kong satoken-auth 注入）。
 */
@Configuration
public class CorsConfig {

    @Value("${cors.allowed-origins:http://localhost:3000,http://localhost:3001,http://localhost:8080}")
    private String allowedOriginsCsv;

    @Value("${cors.allowed-methods:GET,POST,PUT,DELETE,OPTIONS}")
    private String allowedMethodsCsv;

    @Value("${cors.allowed-headers:Authorization,token,Content-Type,X-Requested-With,X-User-Id,X-Username,X-User-Role,X-User-Status,Accept,Origin,Referer,User-Agent}")
    private String allowedHeadersCsv;

    @Value("${cors.allow-credentials:true}")
    private boolean allowCredentials;

    @Value("${cors.max-age:3600}")
    private long maxAge;

    @Bean
    public WebMvcConfigurer corsConfigurer() {
        return new WebMvcConfigurer() {
            @Override
            public void addCorsMappings(CorsRegistry registry) {
                List<String> origins = Arrays.stream(allowedOriginsCsv.split(","))
                        .map(String::trim)
                        .filter(StringUtils::hasText)
                        .toList();
                registry.addMapping("/**")
                        .allowedOrigins(origins.toArray(new String[0]))
                        .allowedMethods(allowedMethodsCsv.split(","))
                        .allowedHeaders(allowedHeadersCsv.split(","))
                        .allowCredentials(allowCredentials)
                        .maxAge(maxAge);
            }
        };
    }
}