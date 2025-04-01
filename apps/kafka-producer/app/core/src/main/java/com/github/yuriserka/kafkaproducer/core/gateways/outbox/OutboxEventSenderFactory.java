package com.github.yuriserka.kafkaproducer.core.gateways.outbox;

import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.stereotype.Component;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.github.yuriserka.kafkaproducer.core.entities.outboxevent.OutboxEvent;
import com.github.yuriserka.kafkaproducer.core.gateways.outbox.kafka.KafkaBrokerEventSender;

@Component
public class OutboxEventSenderFactory {
    private KafkaBrokerEventSender kafkaBrokerEventSender;

    public OutboxEventSenderFactory(
        final ObjectMapper objectMapper,
        final KafkaTemplate<String, String> kafkaTemplate
    ) {
        this.kafkaBrokerEventSender = new KafkaBrokerEventSender(objectMapper, kafkaTemplate);
    }

    public MessageBrokerEventSender create(final OutboxEvent outboxEvent) {
        final var broker = outboxEvent.getMessageBroker();
        return switch (broker) {
            case KAFKA -> kafkaBrokerEventSender;
            default -> throw new IllegalArgumentException(String.format("Broker %s is not supported", broker));
        };
    }
}
