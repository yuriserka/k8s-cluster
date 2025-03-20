package com.github.yuriserka.kafkaproducer.scheduler;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Import;
import org.springframework.kafka.annotation.EnableKafka;
import org.springframework.scheduling.annotation.EnableScheduling;

import com.github.yuriserka.kafkaproducer.core.config.ApplicationPropertySource;
import com.github.yuriserka.kafkaproducer.core.config.JpaConfiguration;

@SpringBootApplication(scanBasePackages = "com.github.yuriserka.kafkaproducer")
@Import(JpaConfiguration.class)
@EnableKafka
@EnableScheduling
@ApplicationPropertySource
public class SchedulerApplication {
	public static void main(String[] args) {
		SpringApplication.run(SchedulerApplication.class, args);
	}
}
