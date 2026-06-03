package com.github.yuriserka.kafkaproducer.core;

import static org.junit.jupiter.api.Assertions.assertNotNull;

import com.github.yuriserka.kafkaproducer.core.support.PostgresTestConfiguration;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.context.ApplicationContext;
import org.springframework.context.annotation.Import;

@SpringBootTest
@Import(PostgresTestConfiguration.class)
class CoreApplicationTest {

  @Autowired
  private ApplicationContext applicationContext;

  @Test
  void contextLoads() {
    assertNotNull(applicationContext, "Spring application context should start");
  }
}
