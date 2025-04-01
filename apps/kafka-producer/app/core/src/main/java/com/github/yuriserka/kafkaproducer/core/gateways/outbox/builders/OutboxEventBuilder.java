package com.github.yuriserka.kafkaproducer.core.gateways.outbox.builders;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.github.yuriserka.kafkaproducer.core.gateways.database.outboxevent.dtos.OutboxEventDto;
import com.github.yuriserka.kafkaproducer.core.gateways.outbox.EventTypes;

import lombok.RequiredArgsConstructor;

@RequiredArgsConstructor
public abstract class OutboxEventBuilder<T> {
    protected final ObjectMapper objectMapper;

    public OutboxEventDto build(Object... args) {
        final var payload = createPayload(args);
        return OutboxEventDto.kafkaEvent(
            getAggregateId(payload),
            getEventType(),
            objectMapper.valueToTree(payload)
        );
    }

    protected abstract String getAggregateId(T payload);

    protected abstract EventTypes getEventType();

    protected abstract T createPayload(Object... args);
}
