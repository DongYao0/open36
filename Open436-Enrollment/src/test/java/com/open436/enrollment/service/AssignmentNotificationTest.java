package com.open436.enrollment.service;

import com.open436.enrollment.entity.Assignment;
import com.open436.enrollment.entity.AssignmentAllocation;
import com.open436.enrollment.entity.AssignmentSubmission;
import com.open436.enrollment.repository.*;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;
import java.util.Optional;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class AssignmentNotificationTest {

    @Mock AssignmentRepository assignmentRepository;
    @Mock AssignmentAllocationRepository allocationRepository;
    @Mock AssignmentSubmissionRepository submissionRepository;
    @Mock EnrollmentRepository enrollmentRepository;
    @InjectMocks AssignmentService service;

    @Test
    void openingAssignmentMarksAllocationRead() {
        AssignmentAllocation allocation = AssignmentAllocation.builder()
                .id(10L).assignmentId(20L).studentId(30L).build();
        Assignment assignment = Assignment.builder()
                .id(20L).title("测试作业").status("active").build();
        when(allocationRepository.findByAssignmentIdAndStudentId(20L, 30L))
                .thenReturn(Optional.of(allocation));
        when(assignmentRepository.findById(20L)).thenReturn(Optional.of(assignment));
        when(submissionRepository.findByAssignmentIdAndStudentId(20L, 30L))
                .thenReturn(Optional.empty());

        Map<String, Object> result = service.getMyAssignmentDetail(30L, 20L);

        assertEquals("测试作业", result.get("title"));
        assertNotNull(allocation.getReadAt());
        verify(allocationRepository).save(allocation);
    }

    @Test
    void reminderMakesAssignmentUnreadAgain() {
        AssignmentSubmission submission = AssignmentSubmission.builder()
                .id(40L).assignmentId(20L).studentId(30L).studentName("测试用户").build();
        AssignmentAllocation allocation = AssignmentAllocation.builder()
                .assignmentId(20L).studentId(30L).readAt(LocalDateTime.now()).build();
        when(submissionRepository.findById(40L)).thenReturn(Optional.of(submission));
        when(allocationRepository.findByAssignmentIdAndStudentId(20L, 30L))
                .thenReturn(Optional.of(allocation));

        service.sendReminder(40L);

        assertNull(allocation.getReadAt());
        assertNotNull(allocation.getRemindedAt());
        verify(allocationRepository).save(allocation);
    }

    @Test
    void badgeCountComesFromPendingActionableAssignments() {
        when(allocationRepository.countPendingActionable(eq(30L), any(LocalDateTime.class)))
                .thenReturn(3L);
        assertEquals(3L, service.getUnreadCount(30L));
    }

    @Test
    void assignmentListMarksOnlyActiveUnsubmittedFutureWorkAsActionable() {
        LocalDateTime now = LocalDateTime.now();
        List<AssignmentAllocation> allocations = List.of(
                AssignmentAllocation.builder().id(1L).assignmentId(11L).studentId(30L).build(),
                AssignmentAllocation.builder().id(2L).assignmentId(12L).studentId(30L).build(),
                AssignmentAllocation.builder().id(3L).assignmentId(13L).studentId(30L).build(),
                AssignmentAllocation.builder().id(4L).assignmentId(14L).studentId(30L).build());
        List<Assignment> assignments = List.of(
                Assignment.builder().id(11L).title("待完成").status("active").deadline(now.plusHours(1)).build(),
                Assignment.builder().id(12L).title("已提交").status("active").deadline(now.plusHours(1)).build(),
                Assignment.builder().id(13L).title("已过期").status("active").deadline(now.minusHours(1)).build(),
                Assignment.builder().id(14L).title("未发布").status("pending").deadline(now.plusHours(1)).build());
        AssignmentSubmission submitted = AssignmentSubmission.builder()
                .assignmentId(12L).studentId(30L).status("submitted").build();

        when(allocationRepository.findByStudentIdOrderByAssignedAtDesc(30L)).thenReturn(allocations);
        when(assignmentRepository.findAllById(anyList())).thenReturn(assignments);
        when(submissionRepository.findByStudentId(30L)).thenReturn(List.of(submitted));

        List<Map<String, Object>> result = service.getMyAssignments(30L);

        assertEquals(List.of(true, false, false, false),
                result.stream().map(item -> item.get("pendingActionable")).toList());
        assertEquals(List.of(false, false, true, true),
                result.stream().map(item -> item.get("expired")).toList());
    }
}
