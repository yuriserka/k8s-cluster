package com.github.yuriserka.kafkaproducer.core.gateways.outbox;

import lombok.Getter;
import lombok.RequiredArgsConstructor;

@RequiredArgsConstructor
public enum EventTypes {
    SEND_MESSAGE_TO_USER("example-topic"),
    SEND_WEATHER_REPORT("example-topic");

    @Getter
    private final String destination;
}
