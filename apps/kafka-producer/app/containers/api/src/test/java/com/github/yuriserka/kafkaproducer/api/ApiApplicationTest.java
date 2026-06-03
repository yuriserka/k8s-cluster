package com.github.yuriserka.kafkaproducer.api;

import com.github.yuriserka.kafkaproducer.core.support.PostgresTestConfiguration;
import org.junit.jupiter.api.Test;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.context.annotation.Import;

@SpringBootTest(classes = ApiApplication.class)
@Import(PostgresTestConfiguration.class)
class ApiApplicationTest {

  @Test
  void contextLoads() {
  }
}
