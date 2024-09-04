package com.github.yuriserka.kafkaproducer.core;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.kafka.annotation.EnableKafka;

import com.github.yuriserka.kafkaproducer.core.config.ApplicationPropertySource;

@SpringBootApplication(scanBasePackages = "com.github.yuriserka.kafkaproducer")
@EnableKafka
@ApplicationPropertySource
public class CoreApplication {
    public static void main(String[] args) {
        SpringApplication.run(CoreApplication.class, args);
    }
}
