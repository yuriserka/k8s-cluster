package com.github.yuriserka.kafkaproducer.core.messaging.example.dtos;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.github.yuriserka.kafkaproducer.core.messaging.dtos.EventDTO;

public record ExampleEventDataDTO(@JsonProperty("user_id") String userId, String name) {
    public static EventDTO<ExampleEventDataDTO> toKafkaEvent(final String id, final String username) {
        return EventDTO.withData("test", new ExampleEventDataDTO(id, username));
    }
}
