package com.github.yuriserka.kafkaproducer.core.messaging.dtos;

import java.time.LocalDateTime;
import java.util.UUID;

public record EventDTO<T>(String id, String type, LocalDateTime timestamp, T data) {
    public static <T> EventDTO<T> withData(final String type, final T data) {
        return new EventDTO<>(UUID.randomUUID().toString(), type, LocalDateTime.now(), data);
    }
}
