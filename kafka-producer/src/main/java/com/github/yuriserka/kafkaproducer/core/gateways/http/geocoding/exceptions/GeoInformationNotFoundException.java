package com.github.yuriserka.kafkaproducer.core.gateways.http.geocoding.exceptions;

import com.github.yuriserka.kafkaproducer.core.exceptions.BusinessException;

public class GeoInformationNotFoundException extends BusinessException {
    public GeoInformationNotFoundException(final String city) {
        super(String.format("Geo information not found for city %s", city));
    }
}
