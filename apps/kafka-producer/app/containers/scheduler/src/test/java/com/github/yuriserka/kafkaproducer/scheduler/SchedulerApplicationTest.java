package com.github.yuriserka.kafkaproducer.scheduler;

import org.junit.jupiter.api.Test;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.context.annotation.Import;

import com.github.yuriserka.kafkaproducer.core.support.PostgresTestConfiguration;

@SpringBootTest(classes = SchedulerApplication.class)
@Import(PostgresTestConfiguration.class)
class SchedulerApplicationTest {

    @Test
    void contextLoads() {
    }
}
