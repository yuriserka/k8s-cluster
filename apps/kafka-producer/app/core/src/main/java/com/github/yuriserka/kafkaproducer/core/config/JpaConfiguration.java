package com.github.yuriserka.kafkaproducer.core.config;

import org.springframework.boot.autoconfigure.domain.EntityScan;
import org.springframework.context.annotation.Configuration;
import org.springframework.data.jpa.repository.config.EnableJpaRepositories;
import org.springframework.transaction.annotation.EnableTransactionManagement;

@Configuration
@EnableTransactionManagement
@EnableJpaRepositories(basePackages = "com.github.yuriserka.kafkaproducer.core.gateways.database")
@EntityScan(basePackages = "com.github.yuriserka.kafkaproducer.core.entities")
public class JpaConfiguration {
}
