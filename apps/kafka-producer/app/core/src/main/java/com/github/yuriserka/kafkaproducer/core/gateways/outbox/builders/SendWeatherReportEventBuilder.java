package com.github.yuriserka.kafkaproducer.core.gateways.outbox.builders;

import java.time.LocalDateTime;
import java.util.UUID;

import org.springframework.stereotype.Component;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.github.yuriserka.kafkaproducer.core.gateways.outbox.EventTypes;
import com.github.yuriserka.kafkaproducer.core.gateways.outbox.dtos.SendWeatherReportPayloadDto;

@Component
public class SendWeatherReportEventBuilder extends OutboxEventBuilder<SendWeatherReportPayloadDto> {
    static final EventTypes EVENT_TYPE = EventTypes.SEND_WEATHER_REPORT;

    public SendWeatherReportEventBuilder(final ObjectMapper objectMapper) {
        super(objectMapper);
    }

    @Override
    protected SendWeatherReportPayloadDto createPayload(final Object... args) {
        final var address = (String) args[0];
        final var temperature = (String) args[1];
        final var windSpeed = (String) args[2];
        final var windDirection = (String) args[3];
        return new SendWeatherReportPayloadDto(
            UUID.randomUUID().toString(),
            address,
            temperature,
            windSpeed,
            windDirection,
            LocalDateTime.now()
        );
    }

    @Override
    protected String getAggregateId(final SendWeatherReportPayloadDto payload) {
        return payload.reportId();
    }

    @Override
    protected EventTypes getEventType() {
        return EVENT_TYPE;
    }
}
