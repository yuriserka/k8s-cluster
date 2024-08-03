package com.github.yuriserka.kafkaproducer.core.gateways.http.openmeteo.exceptions;

import com.github.yuriserka.kafkaproducer.core.exceptions.BusinessException;

public class ForecastInformationNotFoundException extends BusinessException {
    public ForecastInformationNotFoundException(final Double latitude, final Double longitude) {
        super(String.format("Forecast information not found for location (%s, %s)", latitude, longitude));
    }
}
