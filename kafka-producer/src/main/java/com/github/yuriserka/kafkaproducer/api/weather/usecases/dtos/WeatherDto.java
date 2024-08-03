package com.github.yuriserka.kafkaproducer.api.weather.usecases.dtos;

public record WeatherDto(String address, String temperature, String windSpeed, String windDirection) {
}
