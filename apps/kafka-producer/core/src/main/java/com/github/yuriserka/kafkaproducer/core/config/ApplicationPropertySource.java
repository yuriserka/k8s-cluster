package com.github.yuriserka.kafkaproducer.core.config;

import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;

import org.springframework.context.annotation.PropertySource;

@Target(ElementType.TYPE)
@Retention(RetentionPolicy.RUNTIME)
@PropertySource("classpath:application.yaml")
@PropertySource("classpath:application-${spring.profiles.active}.yaml")
public @interface ApplicationPropertySource {
}
