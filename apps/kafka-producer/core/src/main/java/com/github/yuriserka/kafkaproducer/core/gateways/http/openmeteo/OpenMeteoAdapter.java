package com.github.yuriserka.kafkaproducer.core.gateways.http.openmeteo;

import org.springframework.stereotype.Component;

import com.github.yuriserka.kafkaproducer.core.gateways.http.openmeteo.dtos.OpenMeteoForecastDto;
import com.github.yuriserka.kafkaproducer.core.gateways.http.openmeteo.exceptions.ForecastInformationNotFoundException;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;

@RequiredArgsConstructor
@Slf4j
@Component
public class OpenMeteoAdapter {
    private final OpenMeteoForecastHttpClient forecastHttpClient;

    public OpenMeteoForecastDto getWeatherFor(final Double latitude, final Double longitude) {
        log.info("Getting weather for latitude {} and longitude {}", latitude, longitude);
        final var response = forecastHttpClient.getForecast(latitude, longitude, true);

        final var currentWeather = response.getCurrentWeather();
        if (currentWeather == null) {
            throw new ForecastInformationNotFoundException(latitude, longitude);
        }

        final var currentWeatherUnits = response.getCurrentWeatherUnits();

        return new OpenMeteoForecastDto(
            String.format("%.2f %s", currentWeather.temperature(), currentWeatherUnits.temperature()),
            String.format("%.2f %s", currentWeather.windSpeed(), currentWeatherUnits.windSpeed()),
            String.format("%d %s", currentWeather.windDirection(), currentWeatherUnits.windDirection())
        );
    }
}
