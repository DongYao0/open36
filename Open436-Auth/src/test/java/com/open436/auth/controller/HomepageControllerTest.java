package com.open436.auth.controller;

import com.open436.auth.base.BaseApiTest;
import com.open436.auth.dto.LoginRequest;
import org.junit.jupiter.api.Test;
import org.springframework.http.MediaType;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.put;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

/** 验证后台保存的数据可被 Landing 的公开首页接口完整读取。 */
class HomepageControllerTest extends BaseApiTest {

    @Test
    void publicHomepage_ReturnsPersistedModule() throws Exception {
        String token = loginAsAdmin();
        String content = "{\"subText\":\"核心优势\",\"headText\":\"实验室功能.\",\"items\":[{\"title\":\"测试卡片\",\"points\":[\"一条要点\"]}]}";

        mockMvc.perform(put("/api/users/homepage/admin/experiences")
                        .header("token", token)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(content))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(200));

        mockMvc.perform(get("/api/users/homepage/public"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.data.experiences.subText").value("核心优势"))
                .andExpect(jsonPath("$.data.experiences.items[0].title").value("测试卡片"));
    }

    @Test
    void homepageAdminEndpoint_RejectsNonAdmin() throws Exception {
        mockMvc.perform(put("/api/users/homepage/admin/about")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"headText\":\"禁止写入\"}"))
                .andExpect(status().isUnauthorized());
    }

    private String loginAsAdmin() throws Exception {
        LoginRequest request = new LoginRequest();
        request.setUsername("test_admin");
        request.setPassword("test123");
        String response = mockMvc.perform(post("/api/auth/login")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(toJson(request)))
                .andExpect(status().isOk())
                .andReturn().getResponse().getContentAsString();
        return objectMapper.readTree(response).get("data").get("token").asText();
    }
}
