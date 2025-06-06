package com.github.yuriserka.kafkaproducer.api;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Import;
import org.springframework.kafka.annotation.EnableKafka;

import com.github.yuriserka.kafkaproducer.core.config.ApplicationPropertySource;
import com.github.yuriserka.kafkaproducer.core.config.JpaConfiguration;

@SpringBootApplication(scanBasePackages = "com.github.yuriserka.kafkaproducer")
@Import(JpaConfiguration.class)
@EnableKafka
@ApplicationPropertySource
public class ApiApplication {
	public static void main(String[] args) {
		SpringApplication.run(ApiApplication.class, args);
	}
}
