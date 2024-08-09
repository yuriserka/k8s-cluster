package com.github.yuriserka.kafkaproducer.core.gateways.http.openmeteo.dtos;

public record OpenMeteoForecastDto(String temperature, String windSpeed, String windDirection) {
}
