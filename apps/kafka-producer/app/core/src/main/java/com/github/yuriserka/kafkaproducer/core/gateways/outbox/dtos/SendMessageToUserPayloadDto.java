package com.github.yuriserka.kafkaproducer.core.gateways.outbox.dtos;

import com.fasterxml.jackson.annotation.JsonProperty;

public record SendMessageToUserPayloadDto(@JsonProperty("user_id") String userId, String username) {
}