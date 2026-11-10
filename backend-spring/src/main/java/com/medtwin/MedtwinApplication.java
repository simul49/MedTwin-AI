package com.medtwin;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

import java.util.TimeZone;

@SpringBootApplication
public class MedtwinApplication {
    public static void main(String[] args) {
        // MySQL DATETIME columns hold UTC values; keep JDBC conversions aligned.
        TimeZone.setDefault(TimeZone.getTimeZone("UTC"));
        SpringApplication.run(MedtwinApplication.class, args);
    }
}
