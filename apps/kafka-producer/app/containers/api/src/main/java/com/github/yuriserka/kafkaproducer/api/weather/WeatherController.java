package com.github.yuriserka.kafkaproducer.api.weather;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import com.github.yuriserka.kafkaproducer.api.weather.dtos.WeatherDto;
import com.github.yuriserka.kafkaproducer.api.weather.usecases.GetCurrentWeatherForCityUseCase;

import lombok.RequiredArgsConstructor;

@RestController
@RequiredArgsConstructor
@RequestMapping("/weather")
public class WeatherController {
    private final GetCurrentWeatherForCityUseCase currentWeatherForCityUseCase;

    @GetMapping("/current")
    public WeatherDto getWeatherFor(@RequestParam String city) {
        return currentWeatherForCityUseCase.execute(city);
    }
}
