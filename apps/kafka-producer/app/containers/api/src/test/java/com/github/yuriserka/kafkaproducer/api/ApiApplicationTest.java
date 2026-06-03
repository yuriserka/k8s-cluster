package com.github.yuriserka.kafkaproducer.api;

import static org.junit.jupiter.api.Assertions.assertNotNull;

import com.github.yuriserka.kafkaproducer.core.support.PostgresTestConfiguration;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.context.ApplicationContext;
import org.springframework.context.annotation.Import;

@SpringBootTest(classes = ApiApplication.class)
@Import(PostgresTestConfiguration.class)
class ApiApplicationTest {

  @Autowired
  private ApplicationContext applicationContext;

  @Test
  void contextLoads() {
    assertNotNull(applicationContext, "Spring application context should start");
  }
}
