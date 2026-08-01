package com.open436.enrollment;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cloud.client.discovery.EnableDiscoveryClient;

@SpringBootApplication
@EnableDiscoveryClient
public class Open436EnrollmentApplication {

    public static void main(String[] args) {
        SpringApplication.run(Open436EnrollmentApplication.class, args);
    }

}
