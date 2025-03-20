package com.github.yuriserka.kafkaproducer.core.gateways.outbox.builders;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.github.yuriserka.kafkaproducer.core.gateways.database.outboxevent.dtos.OutboxEventDto;
import com.github.yuriserka.kafkaproducer.core.gateways.outbox.EventTypes;

public class SendMessageToUserEventBuilder extends OutboxEventBuilder {
    static final EventTypes EVENT_TYPE = EventTypes.SEND_MESSAGE_TO_USER;

    public SendMessageToUserEventBuilder(final ObjectMapper objectMapper) {
        super(objectMapper);
    }

    public OutboxEventDto build(Object... args) {
        final var payload = createPayload(args);
        return OutboxEventDto.kafkaEvent(payload.get("userId").asText(), EVENT_TYPE, payload);
    }

    private JsonNode createPayload(Object... args) {
        final var userId = (String) args[0];
        final var username = (String) args[1];
        final var payload = objectMapper.createObjectNode();
        payload.set("userId", objectMapper.valueToTree(userId));
        payload.set("username", objectMapper.valueToTree(username));
        return payload;
    }
}
