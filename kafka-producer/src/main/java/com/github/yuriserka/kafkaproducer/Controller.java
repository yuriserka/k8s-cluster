package com.github.yuriserka.kafkaproducer;

import java.time.LocalDateTime;
import java.util.UUID;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RestController;

import com.github.yuriserka.kafkaproducer.dtos.EventDTO;
import com.github.yuriserka.kafkaproducer.dtos.EventDataDTO;
import com.github.yuriserka.kafkaproducer.messaging.ExampleProducer;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;

@RestController
@RequiredArgsConstructor
@Slf4j
public class Controller {
    private final ExampleProducer exampleProducer;

    @GetMapping("/produce/{username}")
    public ResponseEntity<EventDTO<EventDataDTO>> produceMessage(@PathVariable("username") final String username) {
        log.info("Producing message for user {}", username);

        final var event = new EventDTO<>(
                UUID.randomUUID().toString(),
                "test",
                LocalDateTime.now(),
                new EventDataDTO(UUID.randomUUID().toString(), username));

        log.info("Sending message {}", event);

        exampleProducer.sendMessage(event);
        return ResponseEntity.ok(event);
    }
}
