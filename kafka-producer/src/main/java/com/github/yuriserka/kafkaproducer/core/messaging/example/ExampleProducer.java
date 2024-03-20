package com.github.yuriserka.kafkaproducer.core.messaging.example;

import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.stereotype.Component;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.github.yuriserka.kafkaproducer.core.messaging.AbstractKafkaProducer;
import com.github.yuriserka.kafkaproducer.core.messaging.dtos.EventDTO;
import com.github.yuriserka.kafkaproducer.core.messaging.example.dtos.ExampleEventDataDTO;

@Component
public class ExampleProducer extends AbstractKafkaProducer<EventDTO<ExampleEventDataDTO>> {
    public ExampleProducer(final ObjectMapper objectMapper, final KafkaTemplate<String, String> kafkaTemplate) {
        super(objectMapper, kafkaTemplate);
    }

    @Override
    protected String getTopic() {
        return "example-topic";
    }
}
