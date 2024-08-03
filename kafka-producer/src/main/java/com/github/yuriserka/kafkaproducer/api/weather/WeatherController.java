package com.github.yuriserka.kafkaproducer.api.weather;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import com.github.yuriserka.kafkaproducer.api.weather.usecases.GetCurrentWeatherForCityUseCase;
import com.github.yuriserka.kafkaproducer.api.weather.usecases.dtos.WeatherDto;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;

@RestController
@RequiredArgsConstructor
@Slf4j
@RequestMapping("/weather")
public class WeatherController {
    private final GetCurrentWeatherForCityUseCase currentWeatherForCityUseCase;

    @GetMapping("/current")
    public WeatherDto getWeatherFor(@RequestParam String city) {
        final var weatherDto = currentWeatherForCityUseCase.execute(city);
        log.info("Weather for city {}: {}", city, weatherDto);
        return weatherDto;
    }
}
