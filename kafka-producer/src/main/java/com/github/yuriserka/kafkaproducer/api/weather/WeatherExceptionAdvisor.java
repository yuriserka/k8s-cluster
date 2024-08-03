package com.github.yuriserka.kafkaproducer.api.weather;

import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestControllerAdvice;

import com.github.yuriserka.kafkaproducer.api.config.CommonRestAdvice;
import com.github.yuriserka.kafkaproducer.api.config.ExceptionDto;
import com.github.yuriserka.kafkaproducer.core.gateways.http.openmeteo.exceptions.ForecastInformationNotFoundException;
import com.github.yuriserka.kafkaproducer.core.gateways.http.geocoding.exceptions.FailToEncodeCityNameException;
import com.github.yuriserka.kafkaproducer.core.gateways.http.geocoding.exceptions.GeoInformationNotFoundException;

@RestControllerAdvice("com.github.yuriserka.kafkaproducer.api.weather")
public class WeatherExceptionAdvisor extends CommonRestAdvice {
    @ExceptionHandler(ForecastInformationNotFoundException.class)
    @ResponseStatus(HttpStatus.NOT_FOUND)
    public ExceptionDto handleForecastInfoNotFoundException(final ForecastInformationNotFoundException e) {
        return logAndReturnDto("Forecast info not found", e);
    }

    @ExceptionHandler(FailToEncodeCityNameException.class)
    @ResponseStatus(HttpStatus.BAD_REQUEST)
    public ExceptionDto handleFailToEncodeCityNameException(final FailToEncodeCityNameException e) {
        return logAndReturnDto("Fail to parse city name", e);
    }

    @ExceptionHandler(GeoInformationNotFoundException.class)
    @ResponseStatus(HttpStatus.NOT_FOUND)
    public ExceptionDto handleGeoInformationNotFoundException(final GeoInformationNotFoundException e) {
        return logAndReturnDto("Geographic information not found", e);
    }
}
