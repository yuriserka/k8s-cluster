package com.github.yuriserka.kafkaproducer.core.gateways.outbox.kafka;

import org.springframework.stereotype.Component;

import com.github.yuriserka.kafkaproducer.core.gateways.database.outboxevent.dtos.OutboxEventDto;
import com.github.yuriserka.kafkaproducer.core.gateways.outbox.EventTypes;
import com.github.yuriserka.kafkaproducer.core.gateways.outbox.builders.OutboxEventBuilder;
import com.github.yuriserka.kafkaproducer.core.gateways.outbox.builders.SendMessageToUserEventBuilder;
import com.github.yuriserka.kafkaproducer.core.gateways.outbox.builders.SendWeatherReportEventBuilder;

import lombok.RequiredArgsConstructor;

@Component
@RequiredArgsConstructor
public class KafkaBrokerEventTypesFactory {
    private final SendMessageToUserEventBuilder sendMessageToUserEventBuilder;
    private final SendWeatherReportEventBuilder sendWeatherReportEventBuilder;

    public OutboxEventDto create(final EventTypes eventType, final Object... args) {
        final OutboxEventBuilder<?> eventBuilder = switch (eventType) {
            case SEND_MESSAGE_TO_USER -> sendMessageToUserEventBuilder;
            case SEND_WEATHER_REPORT -> sendWeatherReportEventBuilder;
            default -> throw new IllegalArgumentException(String.format("Event type %s is not supported", eventType));
        };
        return eventBuilder.build(args);
    }
}
