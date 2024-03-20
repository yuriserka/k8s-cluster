package com.github.yuriserka.kafkaproducer.api.message.usecase;

import java.util.UUID;

import org.springframework.stereotype.Component;

import com.github.yuriserka.kafkaproducer.core.messaging.example.ExampleProducer;
import com.github.yuriserka.kafkaproducer.core.messaging.example.dtos.ExampleEventDataDTO;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;

@Component
@RequiredArgsConstructor
@Slf4j
public class SendMessageToUserUseCase {
    private final ExampleProducer exampleProducer;

    public void execute(final String username) {
        final var event = ExampleEventDataDTO.toKafkaEvent(UUID.randomUUID().toString(), username);
        log.info("sending event of user {} to kafka {}", username, event);
        exampleProducer.sendMessage(event);
    }
}
