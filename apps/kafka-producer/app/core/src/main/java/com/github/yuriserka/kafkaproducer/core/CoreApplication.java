package com.github.yuriserka.kafkaproducer.core;

import com.github.yuriserka.kafkaproducer.core.config.ApplicationPropertySource;
import com.github.yuriserka.kafkaproducer.core.config.JpaConfiguration;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Import;
import org.springframework.kafka.annotation.EnableKafka;

@SpringBootApplication(scanBasePackages = "com.github.yuriserka.kafkaproducer")
@Import(JpaConfiguration.class)
@EnableKafka
@ApplicationPropertySource
public class CoreApplication {

  public static void main(String[] args) {
    SpringApplication.run(CoreApplication.class, args);
  }
}
