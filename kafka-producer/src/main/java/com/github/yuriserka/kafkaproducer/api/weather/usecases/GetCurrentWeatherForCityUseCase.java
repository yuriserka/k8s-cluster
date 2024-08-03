package com.github.yuriserka.kafkaproducer.api.weather.usecases;

import org.springframework.stereotype.Service;

import com.github.yuriserka.kafkaproducer.api.weather.usecases.dtos.WeatherDto;
import com.github.yuriserka.kafkaproducer.core.gateways.http.geocoding.GeocodingAdapter;
import com.github.yuriserka.kafkaproducer.core.gateways.http.openmeteo.OpenMeteoAdapter;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;

@Service
@RequiredArgsConstructor
@Slf4j
public class GetCurrentWeatherForCityUseCase {
    private final OpenMeteoAdapter openMeteoAdapter;
    private final GeocodingAdapter geocodingAdapter;

    public WeatherDto execute(final String city) {
        log.info("Getting current weather for city {}", city);
        final var geocodingDto = geocodingAdapter.getGeocoding(city);
        final var openMeteoDto = openMeteoAdapter.getWeatherFor(geocodingDto.lat(), geocodingDto.lon());

        return new WeatherDto(
            String.format("%s, %s", geocodingDto.name(), geocodingDto.country()),
            openMeteoDto.temperature(),
            openMeteoDto.windSpeed(),
            openMeteoDto.windDirection()
        );
    }
}
