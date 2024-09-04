package com.github.yuriserka.kafkaproducer.core.gateways.http.geocoding;

import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestParam;

import com.github.yuriserka.kafkaproducer.core.gateways.http.geocoding.dtos.GeocodingHttpResponse;

@FeignClient(name = "geocoding", url = "${spring.http.gateways.geocoding.url}")
public interface GeocodingHttpClient {
    @GetMapping("/v1/search")
    GeocodingHttpResponse getGeocoding(
        @RequestParam("name") String city,
        @RequestParam(value = "count", defaultValue = "1") int limit
    );
}
