package com.open436.auth.service;

import com.open436.auth.dto.ApiResponse;
import com.open436.auth.entity.HojUserMapping;
import com.open436.auth.repository.HojUserMappingRepository;
import com.open436.auth.service.impl.AlgoSyncServiceImpl;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.test.util.ReflectionTestUtils;
import org.springframework.test.web.client.MockRestServiceServer;
import org.springframework.web.client.RestTemplate;

import java.util.Optional;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.mockito.ArgumentMatchers.argThat;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.content;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.method;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.requestTo;
import static org.springframework.test.web.client.response.MockRestResponseCreators.withSuccess;

class AlgoSyncServiceImplTest {

    private AlgoSyncServiceImpl service;
    private HojUserMappingRepository mappingRepository;
    private MockRestServiceServer server;

    @BeforeEach
    void setUp() {
        service = new AlgoSyncServiceImpl();
        mappingRepository = mock(HojUserMappingRepository.class);
        ReflectionTestUtils.setField(service, "hojSyncUrl", "http://hoj.test");
        ReflectionTestUtils.setField(service, "hojApiKey", "test-key");
        ReflectionTestUtils.setField(service, "hojUserMappingRepository", mappingRepository);
        RestTemplate restTemplate = (RestTemplate) ReflectionTestUtils.getField(service, "restTemplate");
        server = MockRestServiceServer.bindTo(restTemplate).build();
    }

    @Test
    void existingMappingIsSentAsStableHojIdentity() {
        HojUserMapping mapping = new HojUserMapping();
        mapping.setAuthUserId(42L);
        mapping.setHojUuid("hoj-uuid-42");
        when(mappingRepository.findByAuthUserId(42L)).thenReturn(Optional.of(mapping));

        server.expect(requestTo("http://hoj.test/api/open436-sync"))
                .andExpect(method(org.springframework.http.HttpMethod.POST))
                .andExpect(content().json("{\"username\":\"田涛\",\"hojUid\":\"hoj-uuid-42\"}"))
                .andRespond(withSuccess("{\"code\":200,\"data\":{\"uid\":\"hoj-uuid-42\"}}",
                        MediaType.APPLICATION_JSON).header(HttpHeaders.AUTHORIZATION, "hoj-token"));

        ApiResponse<String> result = service.syncUserToHoj(42L, "田涛", null, "user");

        assertEquals(200, result.getCode());
        assertEquals("hoj-token", result.getData());
        verify(mappingRepository).save(argThat(saved ->
                saved.getAuthUserId().equals(42L) && "hoj-uuid-42".equals(saved.getHojUuid())));
        server.verify();
    }

    @Test
    void mismatchedResponseUidCannotOverwriteExistingMapping() {
        HojUserMapping mapping = new HojUserMapping();
        mapping.setAuthUserId(42L);
        mapping.setHojUuid("bound-uid");
        when(mappingRepository.findByAuthUserId(42L)).thenReturn(Optional.of(mapping));
        server.expect(requestTo("http://hoj.test/api/open436-sync"))
                .andRespond(withSuccess("{\"data\":{\"uid\":\"other-uid\"}}", MediaType.APPLICATION_JSON)
                        .header(HttpHeaders.AUTHORIZATION, "hoj-token"));

        ApiResponse<String> result = service.syncUserToHoj(42L, "田涛", null, "user");

        assertEquals(500, result.getCode());
        verify(mappingRepository, never()).save(argThat(saved -> true));
        server.verify();
    }
}
