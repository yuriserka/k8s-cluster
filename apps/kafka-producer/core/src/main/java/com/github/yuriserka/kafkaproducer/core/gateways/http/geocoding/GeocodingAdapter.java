package com.github.yuriserka.kafkaproducer.core.gateways.http.geocoding;

import java.io.UnsupportedEncodingException;
import java.net.URLEncoder;

import org.springframework.stereotype.Component;

import com.github.yuriserka.kafkaproducer.core.gateways.http.geocoding.dtos.GeocodingDto;
import com.github.yuriserka.kafkaproducer.core.gateways.http.geocoding.exceptions.FailToEncodeCityNameException;
import com.github.yuriserka.kafkaproducer.core.gateways.http.geocoding.exceptions.GeoInformationNotFoundException;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;

@RequiredArgsConstructor
@Slf4j
@Component
public class GeocodingAdapter {
    private static final int LIMIT = 1;
    private final GeocodingHttpClient httpClient;

    public GeocodingDto getGeocoding(final String city) {
        log.info("Getting geo information for city {}", city);
        final var response = httpClient.getGeocoding(parseCityName(city), LIMIT);

        if (response.getResults() == null || response.getResults().isEmpty()) {
            throw new GeoInformationNotFoundException(city);
        }

        final var result = response.getResults().get(0);
        return new GeocodingDto(
            result.name(),
            result.country(),
            result.latitude(),
            result.longitude()
        );
    }

    private String parseCityName(final String city) {
        try {
            return URLEncoder.encode(city, "UTF-8");
        } catch (final UnsupportedEncodingException e) {
            throw new FailToEncodeCityNameException(city);
        }
    }
}
