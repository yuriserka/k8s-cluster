package com.github.yuriserka.kafkaproducer.core.gateways.http.geocoding.exceptions;

import com.github.yuriserka.kafkaproducer.core.exceptions.BusinessException;

public class FailToEncodeCityNameException extends BusinessException {
    public FailToEncodeCityNameException(final String cityName) {
        super(String.format("Fail to encode city name %s", cityName));
    }
}
