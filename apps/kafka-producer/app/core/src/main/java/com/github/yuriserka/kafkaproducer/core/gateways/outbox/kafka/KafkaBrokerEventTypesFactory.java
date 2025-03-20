package com.github.yuriserka.kafkaproducer.core.gateways.outbox.kafka;

import org.springframework.stereotype.Component;

import com.github.yuriserka.kafkaproducer.core.gateways.database.outboxevent.dtos.OutboxEventDto;
import com.github.yuriserka.kafkaproducer.core.gateways.outbox.EventTypes;
import com.github.yuriserka.kafkaproducer.core.gateways.outbox.builders.SendMessageToUserEventBuilder;

import lombok.RequiredArgsConstructor;

@Component
@RequiredArgsConstructor
public class KafkaBrokerEventTypesFactory {
    private final SendMessageToUserEventBuilder sendMessageToUserEventBuilder;

    public OutboxEventDto create(final EventTypes eventType, final Object... args) {
        return switch (eventType) {
            case SEND_MESSAGE_TO_USER -> sendMessageToUserEventBuilder.build(args);
            default -> throw new IllegalArgumentException(String.format("Event type %s is not supported", eventType));
        };
    }
}
