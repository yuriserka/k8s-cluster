package com.github.yuriserka.kafkaproducer.core.gateways.kafka;

import org.springframework.kafka.core.KafkaTemplate;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;

import lombok.RequiredArgsConstructor;
import lombok.SneakyThrows;
import lombok.extern.slf4j.Slf4j;

@Slf4j
@RequiredArgsConstructor
public abstract class AbstractKafkaProducer<T> {
    private final ObjectMapper objectMapper;
    private final KafkaTemplate<String, String> kafkaTemplate;

    protected abstract String getTopic();

    @SneakyThrows(JsonProcessingException.class)
    public void sendMessage(final T message) {
        final var json = objectMapper.writeValueAsString(message);
        log.info("Sending message to topic {}: {}", getTopic(), json);
        kafkaTemplate.send(getTopic(), json);
    }

    @SneakyThrows(JsonProcessingException.class)
    public void sendMessage(final String key, final T message) {
        final var json = objectMapper.writeValueAsString(message);
        log.info("Sending message with key {} to topic {}: {}", key, getTopic(), json);
        kafkaTemplate.send(getTopic(), key, json);
    }
}
