package com.open436.auth.controller;

import com.open436.auth.base.BaseApiTest;
import org.junit.jupiter.api.Test;
import org.springframework.http.MediaType;

import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.Callable;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

/**
 * 阶段5.2 验收：Auth 注册接口幂等。
 * 1. 同 Key 同内容重复注册 → 返回同一 userId，不重复建号；
 * 2. 同 Key 不同内容 → 409；
 * 3. 同 Key 20 并发 → 恰好一个用户（advisory lock 串行化）。
 */
class RegistrationIdempotencyTest extends BaseApiTest {

    private static final String UNIQUE =
            "lt" + Long.toString(System.nanoTime() % 1000000000L);

    private String body(String username) {
        return "{\"username\":\"" + username + "\",\"password\":\"Test#0436pass\","
                + "\"studentId\":\"200000000000\",\"realName\":\"幂等测试\","
                + "\"phone\":\"170" + UNIQUE.substring(0, 8) + "\",\"major\":\"计算机科学\"}";
    }

    @Test
    void sameKeySameContent_ReturnsSameUserId() throws Exception {
        String key = "idem-" + UNIQUE + "-a";
        String username = UNIQUE + "a";

        String first = mockMvc.perform(post("/api/auth/register")
                        .header("X-Idempotency-Key", key)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(body(username)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.data.id").exists())
                .andReturn().getResponse().getContentAsString();

        String second = mockMvc.perform(post("/api/auth/register")
                        .header("X-Idempotency-Key", key)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(body(username)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.data.id").exists())
                .andReturn().getResponse().getContentAsString();

        String id1 = objectMapper.readTree(first).at("/data/id").asText();
        String id2 = objectMapper.readTree(second).at("/data/id").asText();
        org.junit.jupiter.api.Assertions.assertEquals(id1, id2, "同 Key 重复注册必须返回同一 userId");
    }

    @Test
    void sameKeyDifferentContent_Returns409() throws Exception {
        String key = "idem-" + UNIQUE + "-b";
        mockMvc.perform(post("/api/auth/register")
                        .header("X-Idempotency-Key", key)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(body(UNIQUE + "b")))
                .andExpect(status().isOk());

        // 同 Key，学号内容漂移
        String drifted = "{\"username\":\"" + UNIQUE + "b2\","
                + "\"password\":\"Test#0436pass\",\"studentId\":\"200000000001\","
                + "\"realName\":\"幂等测试\",\"phone\":\"17000000000\",\"major\":\"计算机科学\"}";
        mockMvc.perform(post("/api/auth/register")
                        .header("X-Idempotency-Key", key)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(drifted))
                .andExpect(status().isConflict());
    }

    @Test
    void sameKeyTwentyConcurrent_ExactlyOneUser() throws Exception {
        String key = "idem-" + UNIQUE + "-c";
        String username = UNIQUE + "c";

        ExecutorService pool = Executors.newFixedThreadPool(20);
        List<Callable<String>> tasks = new ArrayList<>();
        for (int i = 0; i < 20; i++) {
            tasks.add(() -> mockMvc.perform(post("/api/auth/register")
                            .header("X-Idempotency-Key", key)
                            .contentType(MediaType.APPLICATION_JSON)
                            .content(body(username)))
                    .andReturn().getResponse().getContentAsString());
        }
        List<Future<String>> results = pool.invokeAll(tasks);
        pool.shutdown();

        // 20 次并发全部受理成功且返回同一 userId；用户名唯一约束保证只有一个用户
        String expectedId = null;
        for (Future<String> f : results) {
            String resp = f.get();
            String id = objectMapper.readTree(resp).at("/data/id").asText();
            org.junit.jupiter.api.Assertions.assertFalse(id.isEmpty(), "响应缺少 userId: " + resp);
            if (expectedId == null) expectedId = id;
            org.junit.jupiter.api.Assertions.assertEquals(expectedId, id, "并发同 Key 返回不一致");
        }
        // 幂等键查询只应有成功结果
        mockMvc.perform(post("/api/auth/register")
                        .header("X-Idempotency-Key", key)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(body(username)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.data.id").value(Integer.parseInt(expectedId)));
    }
}
