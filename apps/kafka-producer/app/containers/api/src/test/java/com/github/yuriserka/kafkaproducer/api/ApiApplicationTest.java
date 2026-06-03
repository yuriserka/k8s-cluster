package com.github.yuriserka.kafkaproducer.api;

import org.junit.jupiter.api.Test;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.context.annotation.Import;

import com.github.yuriserka.kafkaproducer.core.support.PostgresTestConfiguration;

@SpringBootTest(classes = ApiApplication.class)
@Import(PostgresTestConfiguration.class)
class ApiApplicationTest {

    @Test
    void contextLoads() {
    }
}
