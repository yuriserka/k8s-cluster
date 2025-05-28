package com.github.yuriserka.kafkaproducer.core.gateways.outbox.dtos;

import java.time.LocalDateTime;

import com.fasterxml.jackson.annotation.JsonProperty;

public record SendWeatherReportPayloadDto(
    @JsonProperty("report_id") String reportId,
    String address,
    String temperature,
    @JsonProperty("wind_speed") String windSpeed,
    @JsonProperty("wind_direction") String windDirection,
    LocalDateTime timestamp
) {
}
