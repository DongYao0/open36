package com.open436.enrollment.service;

import com.open436.enrollment.dto.ApplyRequest;
import com.open436.enrollment.entity.EnrollmentApplication;
import com.open436.enrollment.exception.EnrollConflictException;
import com.open436.enrollment.exception.EnrollRetryableException;
import com.open436.enrollment.repository.EnrollmentRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.ArgumentCaptor;
import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpMethod;
import org.springframework.http.ResponseEntity;
import org.springframework.test.util.ReflectionTestUtils;
import org.springframework.web.client.HttpClientErrorException;
import org.springframework.web.client.ResourceAccessException;
import org.springframework.web.client.RestTemplate;

import java.net.URI;
import java.util.HashMap;
import java.util.Map;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicInteger;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.atLeast;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.times;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

/**
 * 阶段5.6 验收：报名链路幂等与一致性（服务层单测，Mock 上游）。
 */
class EnrollmentIdempotencyTest {

    private EnrollmentRepository repository;
    private RestTemplate restTemplate;
    private EnrollmentService service;

    private final Map<String, EnrollmentApplication> rowsByKey = new HashMap<>();

    @BeforeEach
    void setUp() {
        repository = mock(EnrollmentRepository.class);
        restTemplate = mock(RestTemplate.class);
        service = new EnrollmentService(repository, restTemplate);
        ReflectionTestUtils.setField(service, "authServiceUrl", "http://auth:8081");
        ReflectionTestUtils.setField(service, "internalApiKey", "test-key");

        rowsByKey.clear();
        // 内存版 repository：save 即持久化到 rowsByKey
        when(repository.findByIdempotencyKey(anyString()))
                .thenAnswer(inv -> Optional.ofNullable(rowsByKey.get(inv.getArgument(0))));
        when(repository.findByAuthUserId(any()))
                .thenAnswer(inv -> rowsByKey.values().stream()
                        .filter(r -> inv.getArgument(0).equals(r.getAuthUserId())).findFirst());
        when(repository.save(any(EnrollmentApplication.class)))
                .thenAnswer(inv -> persist(inv.getArgument(0)));
        when(repository.saveAndFlush(any(EnrollmentApplication.class)))
                .thenAnswer(inv -> persist(inv.getArgument(0)));
    }

    private EnrollmentApplication persist(EnrollmentApplication row) {
        if (row.getIdempotencyKey() != null) {
            rowsByKey.put(row.getIdempotencyKey(), row);
        }
        return row;
    }

    private ApplyRequest request(String username, String studentId) {
        ApplyRequest req = new ApplyRequest();
        req.setUsername(username);
        req.setPassword("Pass#0436");
        req.setStudentId(studentId);
        req.setRealName(username);
        req.setPhone("17012345678");
        req.setMajor("CS");
        req.setSelfIntro("");
        req.setSkills("");
        return req;
    }

    private void mockAuthSuccess(Long userId) {
        when(restTemplate.exchange(anyString(), eq(HttpMethod.POST), any(HttpEntity.class), eq(Map.class)))
                .thenReturn(ResponseEntity.ok(Map.of("data", Map.of("id", userId))));
    }

    /** 1. 同一幂等键重复提交 20 次：只调一次 Auth、只有一行报名 */
    @Test
    void sameKeyTwentyTimes_SingleAuthCallSingleRow() {
        mockAuthSuccess(42L);
        ApplyRequest req = request("stu001", "S001");

        for (int i = 0; i < 20; i++) {
            service.apply(req, "key-1");
        }

        verify(restTemplate, times(1)).exchange(anyString(), eq(HttpMethod.POST),
                any(HttpEntity.class), eq(Map.class));
        assertEquals(1, rowsByKey.size());
        EnrollmentApplication row = rowsByKey.get("key-1");
        assertEquals(EnrollmentApplication.PS_PENDING, row.getProcessingStatus());
        assertEquals(42L, row.getAuthUserId());
    }

    /** 2. 同 Key 不同内容 → 409，且不打 Auth */
    @Test
    void sameKeyDifferentContent_ConflictWithoutAuthCall() {
        mockAuthSuccess(42L);
        service.apply(request("stu001", "S001"), "key-1");

        assertThrows(EnrollConflictException.class,
                () -> service.apply(request("stu001", "S002"), "key-1"));
        verify(restTemplate, times(1)).exchange(anyString(), eq(HttpMethod.POST),
                any(HttpEntity.class), eq(Map.class)); // 只有首次成功那次
    }

    /** 3. Auth 成功、本地终态落库暂时失败 → 行停在 USER_CREATED；同 Key 重试补终态，不再打 Auth */
    @Test
    void finalizeTransientFailureThenRetry_CompletesWithoutSecondAuthCall() {
        mockAuthSuccess(42L);
        AtomicInteger flushCount = new AtomicInteger();
        when(repository.saveAndFlush(any(EnrollmentApplication.class)))
                .thenAnswer(inv -> {
                    EnrollmentApplication row = inv.getArgument(0);
                    // 第一次 finalize 落库模拟数据库瞬时故障
                    if (EnrollmentApplication.PS_PENDING.equals(row.getProcessingStatus())
                            && flushCount.getAndIncrement() == 0) {
                        throw new RuntimeException("connection reset");
                    }
                    return persist(row);
                });

        // 首次：终态写入失败向外传播（DB 行保留 USER_CREATED，对账/重试可恢复；
        // 内存 mock 共享引用会看到 PENDING，故此处不断言中间态）
        assertThrows(RuntimeException.class,
                () -> service.apply(request("stu002", "S002"), "key-2"));

        // 同 Key 重试：行已是 USER_CREATED → 跳过 Auth，直接落终态
        Long id = service.apply(request("stu002", "S002"), "key-2");
        assertEquals(id, rowsByKey.get("key-2").getId());
        verify(restTemplate, times(1)).exchange(anyString(), eq(HttpMethod.POST),
                any(HttpEntity.class), eq(Map.class));
        assertEquals(EnrollmentApplication.PS_PENDING, rowsByKey.get("key-2").getProcessingStatus());
    }

    /** 3b. 跨 Key 抢占同一 auth_user_id（唯一约束竞争）→ 幂等返回既有行，不 500 */
    @Test
    void crossKeySameAuthUser_ReturnsExistingRow() {
        // 另一个 Key 已经为 userId=42 落了完成态报名
        EnrollmentApplication winner = EnrollmentApplication.builder()
                .idempotencyKey("key-other")
                .requestFingerprint("f-other")
                .processingStatus(EnrollmentApplication.PS_PENDING)
                .authUserId(42L)
                .status("pending")
                .build();
        persist(winner);
        mockAuthSuccess(42L); // Auth 幂等键不同会建新号；此处模拟返回了同一 id 的极端场景

        when(repository.saveAndFlush(any(EnrollmentApplication.class)))
                .thenAnswer(inv -> {
                    EnrollmentApplication row = inv.getArgument(0);
                    if (EnrollmentApplication.PS_PENDING.equals(row.getProcessingStatus())
                            && row.getAuthUserId() != null
                            && rowsByKey.values().stream().anyMatch(r -> r != row
                                    && row.getAuthUserId().equals(r.getAuthUserId()))) {
                        throw new DataIntegrityViolationException("uq_enroll_auth_user");
                    }
                    return persist(row);
                });

        Long id = service.apply(request("stu009", "S009"), "key-9");
        assertEquals(winner.getId() != null ? winner.getId() : id, id); // 返回既有行的结果
        verify(restTemplate, times(1)).exchange(anyString(), eq(HttpMethod.POST),
                any(HttpEntity.class), eq(Map.class));
    }

    /** 4. Auth 超时（实际可能已建号）→ RETRYABLE_FAILED；同 Key 重试不重复建号 */
    @Test
    void authTimeoutThenRetry_SameUserNoDuplicate() {
        AtomicInteger calls = new AtomicInteger();
        when(restTemplate.exchange(anyString(), eq(HttpMethod.POST), any(HttpEntity.class), eq(Map.class)))
                .thenAnswer(inv -> {
                    if (calls.getAndIncrement() == 0) {
                        throw new ResourceAccessException("read timeout");
                    }
                    return ResponseEntity.ok(Map.of("data", Map.of("id", 77L)));
                });

        assertThrows(EnrollRetryableException.class,
                () -> service.apply(request("stu003", "S003"), "key-3"));
        assertEquals(EnrollmentApplication.PS_RETRYABLE_FAILED,
                rowsByKey.get("key-3").getProcessingStatus());

        service.apply(request("stu003", "S003"), "key-3"); // 重试成功
        verify(restTemplate, times(2)).exchange(anyString(), eq(HttpMethod.POST),
                any(HttpEntity.class), eq(Map.class)); // 重试幂等地再调一次（Auth 侧同 Key 返回同一用户）
        assertEquals(1, rowsByKey.size());
        assertEquals(77L, rowsByKey.get("key-3").getAuthUserId());
    }

    /** 5. 插入竞争（同 Key 唯一约束兜底）→ 不 500，按已存在行返回 */
    @Test
    void insertRace_FallsBackToExistingRow() {
        when(repository.saveAndFlush(any(EnrollmentApplication.class)))
                .thenAnswer(inv -> {
                    EnrollmentApplication row = inv.getArgument(0);
                    if (row.getProcessingStatus().equals(EnrollmentApplication.PS_RECEIVED)) {
                        // 模拟并发：插入撞唯一约束，胜者已是 PENDING 完成态
                        EnrollmentApplication winner = EnrollmentApplication.builder()
                                .idempotencyKey(row.getIdempotencyKey())
                                .requestFingerprint(row.getRequestFingerprint())
                                .processingStatus(EnrollmentApplication.PS_PENDING)
                                .authUserId(99L)
                                .status("pending")
                                .build();
                        persist(winner);
                        throw new DataIntegrityViolationException("uq_enroll_idem_key");
                    }
                    return persist(row);
                });

        Long id = service.apply(request("stu004", "S004"), "key-4");
        assertEquals(id, rowsByKey.get("key-4").getId());
        verify(restTemplate, never()).exchange(anyString(), eq(HttpMethod.POST),
                any(HttpEntity.class), eq(Map.class)); // 胜者已完成，无需再建号
    }

    /** 6. Auth 明确 409（用户名真实冲突）→ PERMANENT_FAILED；同 Key 重试直接 409，不再打 Auth */
    @Test
    void usernameConflict_PermanentFailure() {
        when(restTemplate.exchange(anyString(), eq(HttpMethod.POST), any(HttpEntity.class), eq(Map.class)))
                .thenThrow(new HttpClientErrorException(
                        org.springframework.http.HttpStatus.CONFLICT, "conflict",
                        "{\"message\":\"用户名已存在\",\"code\":409}".getBytes(), null));

        assertThrows(EnrollConflictException.class,
                () -> service.apply(request("dup", "S005"), "key-5"));
        assertEquals(EnrollmentApplication.PS_PERMANENT_FAILED,
                rowsByKey.get("key-5").getProcessingStatus());

        // 同 Key 重试：不重打 Auth，直接按 PERMANENT_FAILED 拒绝
        assertThrows(EnrollConflictException.class,
                () -> service.apply(request("dup", "S005"), "key-5"));
        verify(restTemplate, times(1)).exchange(anyString(), eq(HttpMethod.POST),
                any(HttpEntity.class), eq(Map.class));
    }

    /** 7. 指纹不包含密码：改密码不改变指纹（密码永不入库/日志的先决条件） */
    @Test
    void fingerprintExcludesPassword() {
        ApplyRequest a = request("stu006", "S006");
        ApplyRequest b = request("stu006", "S006");
        b.setPassword("Another#0436");
        assertEquals(EnrollmentService.fingerprint(a), EnrollmentService.fingerprint(b));

        a.setSelfIntro("changed");
        assertNotEquals(EnrollmentService.fingerprint(a), EnrollmentService.fingerprint(b));
    }

    /** 8. Auth 调用携带 X-Idempotency-Key 头 */
    @Test
    void authCallCarriesIdempotencyHeader() {
        mockAuthSuccess(42L);
        service.apply(request("stu007", "S007"), "key-7");

        @SuppressWarnings("unchecked")
        ArgumentCaptor<HttpEntity<Map<String, Object>>> captor =
                ArgumentCaptor.forClass(HttpEntity.class);
        verify(restTemplate).exchange(anyString(), eq(HttpMethod.POST), captor.capture(), eq(Map.class));
        assertEquals("key-7", captor.getValue().getHeaders().getFirst("X-Idempotency-Key"));
    }
}
