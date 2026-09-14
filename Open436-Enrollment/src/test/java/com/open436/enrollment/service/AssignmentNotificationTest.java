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
    void unreadCountComesFromAllocationState() {
        when(allocationRepository.countByStudentIdAndReadAtIsNull(30L)).thenReturn(3L);
        assertEquals(3L, service.getUnreadCount(30L));
    }
}
