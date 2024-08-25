package com.github.yuriserka.kafkaproducer.core.gateways.http.openmeteo.dtos;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;

import lombok.Data;

@Data
@JsonIgnoreProperties(ignoreUnknown = true)
public class OpenMeteoForecastHttpResponse {
    @JsonProperty("current_weather_units")
    CurrentWeatherUnits currentWeatherUnits;

    @JsonProperty("current_weather")
    CurrentWeather currentWeather;

    public static record CurrentWeatherUnits(
            String temperature,
            @JsonProperty("windspeed") String windSpeed,
            @JsonProperty("winddirection") String windDirection
    ) {}

    public static record CurrentWeather(
        Double temperature,
        @JsonProperty("windspeed") Double windSpeed,
        @JsonProperty("winddirection") int windDirection
    ) {}
}
