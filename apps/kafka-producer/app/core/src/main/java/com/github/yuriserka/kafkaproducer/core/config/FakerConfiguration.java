package com.github.yuriserka.kafkaproducer.core.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import net.datafaker.Faker;

@Configuration
public class FakerConfiguration {
    @Bean
    Faker faker() {
        return new Faker();
    }
}
