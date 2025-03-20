package com.github.yuriserka.kafkaproducer.api.weather.usecases;

import org.springframework.stereotype.Service;

import com.github.yuriserka.kafkaproducer.api.weather.dtos.WeatherDto;
import com.github.yuriserka.kafkaproducer.core.gateways.database.outboxevent.OutboxEventDatabaseAdapter;
import com.github.yuriserka.kafkaproducer.core.gateways.http.geocoding.GeocodingAdapter;
import com.github.yuriserka.kafkaproducer.core.gateways.http.openmeteo.OpenMeteoAdapter;
import com.github.yuriserka.kafkaproducer.core.gateways.outbox.EventTypes;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;

@Service
@RequiredArgsConstructor
@Slf4j
public class GetCurrentWeatherForCityUseCase {
    private final OpenMeteoAdapter openMeteoAdapter;
    private final GeocodingAdapter geocodingAdapter;
    private final OutboxEventDatabaseAdapter outboxEventDatabaseAdapter;

    public WeatherDto execute(final String city) {
        log.info("Getting current weather for city {}", city);
        final var geocodingDto = geocodingAdapter.getGeocoding(city);
        final var openMeteoDto = openMeteoAdapter.getWeatherFor(geocodingDto.lat(), geocodingDto.lon());

        final var currentWeather = new WeatherDto(
            String.format("%s, %s", geocodingDto.name(), geocodingDto.country()),
            openMeteoDto.temperature(),
            openMeteoDto.windSpeed(),
            openMeteoDto.windDirection()
        );

        log.info("Weather for city {}: {}", city, currentWeather);

        outboxEventDatabaseAdapter.saveFromEventType(EventTypes.SEND_WEATHER_REPORT, currentWeather);
        return currentWeather;
    }
}
