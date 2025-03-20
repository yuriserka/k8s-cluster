package com.github.yuriserka.kafkaproducer.core.gateways.outbox.builders;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.github.yuriserka.kafkaproducer.core.gateways.database.outboxevent.dtos.OutboxEventDto;

import lombok.RequiredArgsConstructor;

@RequiredArgsConstructor
public abstract class OutboxEventBuilder {
    protected final ObjectMapper objectMapper;

    public abstract OutboxEventDto build(Object... args);
}
