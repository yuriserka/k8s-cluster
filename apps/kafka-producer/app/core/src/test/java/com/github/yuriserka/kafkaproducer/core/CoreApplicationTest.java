package com.github.yuriserka.kafkaproducer.core;

import com.github.yuriserka.kafkaproducer.core.support.PostgresTestConfiguration;
import org.junit.jupiter.api.Test;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.context.annotation.Import;

@SpringBootTest
@Import(PostgresTestConfiguration.class)
class CoreApplicationTest {

  @Test
  void contextLoads() {
  }
}
