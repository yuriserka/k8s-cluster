package com.github.yuriserka.kafkaproducer.dtos;

import com.fasterxml.jackson.annotation.JsonProperty;

import lombok.Value;

@Value
public class EventDataDTO {
    @JsonProperty("user_id")
    String userId;

    String name;
}
