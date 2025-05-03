package com.github.yuriserka.kafkaproducer.core.gateways.outbox.kafka;

import java.time.LocalDateTime;
import java.util.UUID;

import org.springframework.kafka.core.KafkaTemplate;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.github.yuriserka.kafkaproducer.core.entities.outboxevent.OutboxEvent;
import com.github.yuriserka.kafkaproducer.core.gateways.outbox.MessageBrokerEventSender;

import lombok.RequiredArgsConstructor;
import lombok.SneakyThrows;
import lombok.extern.slf4j.Slf4j;

@RequiredArgsConstructor
@Slf4j
public class KafkaBrokerEventSender implements MessageBrokerEventSender {
    private final ObjectMapper objectMapper;
    private final KafkaTemplate<String, String> kafkaTemplate;

    @Override
    @SneakyThrows(JsonProcessingException.class)
    public void emit(final OutboxEvent event) {
        final var json = objectMapper.writeValueAsString(new EmittedEvent(event));
        log.info("Sending message to topic {}: {}", event.getDestination(), json);
        kafkaTemplate.send(event.getDestination(), json);
    }

    protected record EmittedEvent(
        Long id,
        @JsonProperty("event_id") String eventId,
        @JsonProperty("event_type") String eventType,
        JsonNode payload,
        @JsonProperty("created_at") LocalDateTime createdAt
    ) {
        public EmittedEvent(final OutboxEvent event) {
            this(
                event.getId(),
                UUID.randomUUID().toString(),
                event.getEventType(),
                event.getPayload(),
                event.getCreatedAt()
            );
        }
    }
}
