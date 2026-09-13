package com.open436.enrollment.config;

import lombok.extern.slf4j.Slf4j;
import org.apache.hc.client5.http.config.RequestConfig;
import org.apache.hc.client5.http.impl.classic.CloseableHttpClient;
import org.apache.hc.client5.http.impl.classic.HttpClients;
import org.apache.hc.client5.http.impl.io.PoolingHttpClientConnectionManagerBuilder;
import org.apache.hc.core5.util.TimeValue;
import org.apache.hc.core5.util.Timeout;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.client.HttpComponentsClientHttpRequestFactory;
import org.springframework.web.client.RestTemplate;

/**
 * 服务间 HTTP 客户端（阶段5.4）
 *
 * 替代 new RestTemplate()：
 *  - 连接池：总 40 / 每上游 20（Auth 是唯一上游，到达上游的并发上限=20）；
 *  - 连接超时 2s / 响应超时 5s：Auth 不可达时快速失败，
 *    不长时间占用报名线程与数据库连接；
 *  - 连接复用避免每次请求重建 TCP。
 *
 * 不在此层做盲目自动重试——仅带幂等键的注册请求允许有限重试，
 * 重试语义在 EnrollmentService 内显式控制。
 */
@Slf4j
@Configuration
public class HttpClientConfig {

    @Bean
    public RestTemplate enrollmentRestTemplate() {
        var cm = PoolingHttpClientConnectionManagerBuilder.create()
                .setMaxConnTotal(40)
                .setMaxConnPerRoute(20)
                .build();

        RequestConfig requestConfig = RequestConfig.custom()
                .setConnectionRequestTimeout(Timeout.ofSeconds(2))  // 从池里拿连接最多等2s
                .setConnectTimeout(Timeout.ofSeconds(2))
                .setResponseTimeout(Timeout.ofSeconds(5))
                .build();

        CloseableHttpClient httpClient = HttpClients.custom()
                .setConnectionManager(cm)
                .setDefaultRequestConfig(requestConfig)
                .evictIdleConnections(TimeValue.ofSeconds(30))
                .build();

        RestTemplate restTemplate = new RestTemplate(
                new HttpComponentsClientHttpRequestFactory(httpClient));
        log.info("Enrollment RestTemplate 已配置连接池(40/20)与超时(connect=2s, read=5s)");
        return restTemplate;
    }
}
