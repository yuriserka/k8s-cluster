package com.github.yuriserka.kafkaproducer.core.gateways.outbox.dtos;

import java.time.LocalDateTime;

import com.fasterxml.jackson.annotation.JsonProperty;

public record SendWeatherReportPayloadDto(
    @JsonProperty("report_id") String reportId,
    String address,
    String temperature,
    String windSpeed,
    String windDirection,
    LocalDateTime timestamp
) {
}
