package com.github.yuriserka.kafkaproducer.core.gateways.http.openmeteo;

import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestParam;

import com.github.yuriserka.kafkaproducer.core.gateways.http.openmeteo.dtos.OpenMeteoForecastHttpResponse;

@FeignClient(name = "openmeteo-forecast", url = "${spring.http.gateways.openmeteo.forecast.url}")
public interface OpenMeteoForecastHttpClient {
    @GetMapping
    OpenMeteoForecastHttpResponse getForecast(
        @RequestParam(value = "latitude") Double latitude,
        @RequestParam(value = "longitude") Double longitude,
        @RequestParam(value = "current_weather", defaultValue = "true") Boolean current
    );
}
