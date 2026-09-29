package com.open436.enrollment;

import org.junit.jupiter.api.Test;

import java.util.TimeZone;

import static org.junit.jupiter.api.Assertions.assertEquals;

class Open436EnrollmentApplicationTest {

    @Test
    void configuresBeijingAsDefaultTimeZone() {
        TimeZone original = TimeZone.getDefault();
        try {
            TimeZone.setDefault(TimeZone.getTimeZone("UTC"));

            Open436EnrollmentApplication.configureDefaultTimeZone();

            assertEquals("Asia/Shanghai", TimeZone.getDefault().getID());
        } finally {
            TimeZone.setDefault(original);
        }
    }
}
