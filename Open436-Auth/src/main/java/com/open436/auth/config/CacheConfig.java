package com.open436.auth.config;

import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.extern.slf4j.Slf4j;
import org.springframework.cache.Cache;
import org.springframework.cache.annotation.CachingConfigurer;
import org.springframework.cache.annotation.EnableCaching;
import org.springframework.cache.interceptor.CacheErrorHandler;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.data.redis.cache.RedisCacheConfiguration;
import org.springframework.data.redis.cache.RedisCacheManager;
import org.springframework.data.redis.connection.RedisConnectionFactory;
import org.springframework.data.redis.serializer.GenericJackson2JsonRedisSerializer;
import org.springframework.data.redis.serializer.RedisSerializationContext;
import org.springframework.data.redis.serializer.StringRedisSerializer;

import java.time.Duration;
import java.util.Map;

/**
 * 缓存配置
 * 配置 Redis 缓存管理器 + 各缓存空间的独立 TTL + 故障降级
 *
 * 降级策略（阶段3）：Redis 不可用时缓存读写失败只告警、不抛出，
 * @Cacheable 方法照常执行查库——首页等公共接口不能因缓存故障白屏。
 */
@Slf4j
@Configuration
@EnableCaching
public class CacheConfig implements CachingConfigurer {

    /** 首页公共内容缓存（毫秒级预算外的公共读，TTL 120s 平衡时效与 QPS） */
    public static final String CACHE_HOMEPAGE_PUBLIC = "homepagePublic";
    public static final Duration HOMEPAGE_PUBLIC_TTL = Duration.ofSeconds(120);

    /**
     * 配置 Redis 缓存管理器
     * @param connectionFactory Redis 连接工厂
     * @return RedisCacheManager
     */
    @Bean
    public RedisCacheManager cacheManager(
            RedisConnectionFactory connectionFactory,
            ObjectMapper applicationObjectMapper) {
        GenericJackson2JsonRedisSerializer valueSerializer =
            GenericJackson2JsonRedisSerializer.builder()
                .objectMapper(applicationObjectMapper.copy())
                .defaultTyping(true)
                .build();

        RedisCacheConfiguration common = RedisCacheConfiguration.defaultCacheConfig()
            .entryTtl(Duration.ofMinutes(30))  // 缓存过期时间：30分钟
            .serializeKeysWith(
                RedisSerializationContext.SerializationPair.fromSerializer(
                    new StringRedisSerializer()
                )
            )
            .serializeValuesWith(
                RedisSerializationContext.SerializationPair.fromSerializer(
                    valueSerializer
                )
            );

        return RedisCacheManager.builder(connectionFactory)
            .cacheDefaults(common)
            .withInitialCacheConfigurations(Map.of(
                // 首页公共读：短 TTL，管理端保存/重置时主动驱逐
                CACHE_HOMEPAGE_PUBLIC, common.entryTtl(HOMEPAGE_PUBLIC_TTL)
            ))
            .build();
    }

    /**
     * 缓存故障降级：Redis 宕机/超时时记 warn 并吞掉异常，
     * 业务侧退化为直查 PostgreSQL，公共页面保持可用。
     */
    @Override
    public CacheErrorHandler errorHandler() {
        return new CacheErrorHandler() {
            @Override
            public void handleCacheGetError(RuntimeException e, Cache cache, Object key) {
                log.warn("缓存读取失败（降级直查DB）cache={} key={} err={}", cache.getName(), key, e.getMessage());
            }

            @Override
            public void handleCachePutError(RuntimeException e, Cache cache, Object key, Object value) {
                log.warn("缓存写入失败（忽略）cache={} key={} err={}", cache.getName(), key, e.getMessage());
            }

            @Override
            public void handleCacheEvictError(RuntimeException e, Cache cache, Object key) {
                log.warn("缓存驱逐失败（TTL 兜底）cache={} key={} err={}", cache.getName(), key, e.getMessage());
            }

            @Override
            public void handleCacheClearError(RuntimeException e, Cache cache) {
                log.warn("缓存清空失败（TTL 兜底）cache={} err={}", cache.getName(), e.getMessage());
            }
        };
    }
}
