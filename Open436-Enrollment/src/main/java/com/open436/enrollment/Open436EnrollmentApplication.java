package com.open436.enrollment;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cloud.client.discovery.EnableDiscoveryClient;
import org.springframework.scheduling.annotation.EnableScheduling;

import java.util.TimeZone;

@SpringBootApplication
@EnableDiscoveryClient
@EnableScheduling
public class Open436EnrollmentApplication {

    static final String DEFAULT_TIME_ZONE = "Asia/Shanghai";

    public static void main(String[] args) {
        configureDefaultTimeZone();
        SpringApplication.run(Open436EnrollmentApplication.class, args);
    }

    static void configureDefaultTimeZone() {
        TimeZone.setDefault(TimeZone.getTimeZone(DEFAULT_TIME_ZONE));
    }
}
