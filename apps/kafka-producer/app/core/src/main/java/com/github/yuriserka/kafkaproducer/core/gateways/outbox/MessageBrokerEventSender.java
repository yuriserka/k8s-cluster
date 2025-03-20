package com.github.yuriserka.kafkaproducer.core.gateways.outbox;

import com.github.yuriserka.kafkaproducer.core.entities.outboxevent.OutboxEvent;

public interface MessageBrokerEventSender {
    void emit(final OutboxEvent message);
}
