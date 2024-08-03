package com.github.yuriserka.kafkaproducer.core.gateways.http.geocoding.dtos;

import java.util.List;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;

import lombok.Data;

@JsonIgnoreProperties(ignoreUnknown = true)
@Data
public class GeocodingHttpResponse {
    List<Result> results;

    public static record Result(
        Long id,
        String name,
        Double latitude,
        Double longitude,
        Double elevation,

        @JsonProperty("country_code") String countryCode,
        String country,
        String timezone
    ) {}
}
