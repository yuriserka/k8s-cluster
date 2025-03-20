package com.github.yuriserka.kafkaproducer.core.gateways.outbox;

import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.stereotype.Component;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.github.yuriserka.kafkaproducer.core.entities.outboxevent.OutboxEvent;
import com.github.yuriserka.kafkaproducer.core.gateways.outbox.kafka.KafkaBrokerEventSender;

import lombok.RequiredArgsConstructor;

@Component
@RequiredArgsConstructor
public class OutboxEventSenderFactory {
    private final ObjectMapper objectMapper;
    private final KafkaTemplate<String, String> kafkaTemplate;

    public MessageBrokerEventSender create(final OutboxEvent outboxEvent) {
        final var broker = outboxEvent.getMessageBroker();
        return switch (broker) {
            case KAFKA -> new KafkaBrokerEventSender(objectMapper, kafkaTemplate);
            default -> throw new IllegalArgumentException(String.format("Broker %s is not supported", broker));
        };
    }
}
