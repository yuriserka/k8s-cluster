package com.github.yuriserka.kafkaproducer.core.gateways.outbox.builders;

import org.springframework.stereotype.Component;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.github.yuriserka.kafkaproducer.core.gateways.outbox.EventTypes;
import com.github.yuriserka.kafkaproducer.core.gateways.outbox.dtos.SendMessageToUserPayloadDto;

@Component
public class SendMessageToUserEventBuilder extends OutboxEventBuilder<SendMessageToUserPayloadDto> {
    static final EventTypes EVENT_TYPE = EventTypes.SEND_MESSAGE_TO_USER;

    public SendMessageToUserEventBuilder(final ObjectMapper objectMapper) {
        super(objectMapper);
    }

    @Override
    protected SendMessageToUserPayloadDto createPayload(final Object... args) {
        final var userId = (String) args[0];
        final var username = (String) args[1];
        return new SendMessageToUserPayloadDto(userId, username);
    }

    @Override
    protected EventTypes getEventType() {
        return EVENT_TYPE;
    }

    @Override
    protected String getAggregateId(final SendMessageToUserPayloadDto payload) {
        return payload.userId();
    }
}
