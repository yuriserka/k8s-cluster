package com.github.yuriserka.kafkaproducer.core.gateways.kafka.example;

import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.stereotype.Component;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.github.yuriserka.kafkaproducer.core.gateways.kafka.AbstractKafkaProducer;
import com.github.yuriserka.kafkaproducer.core.messaging.dtos.EventDTO;
import com.github.yuriserka.kafkaproducer.core.messaging.example.dtos.ExampleEventDataDTO;

@Component
public class ExampleKafkaProducer extends AbstractKafkaProducer<EventDTO<ExampleEventDataDTO>> {
    public ExampleKafkaProducer(final ObjectMapper objectMapper, final KafkaTemplate<String, String> kafkaTemplate) {
        super(objectMapper, kafkaTemplate);
    }

    @Override
    protected String getTopic() {
        return "example-topic";
    }
}
