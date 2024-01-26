package com.github.yuriserka.kafkaproducer.messaging;

import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.stereotype.Component;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.github.yuriserka.kafkaproducer.dtos.EventDTO;
import com.github.yuriserka.kafkaproducer.dtos.EventDataDTO;

@Component
public class ExampleProducer extends AbstractKafkaProducer<EventDTO<EventDataDTO>> {
    public ExampleProducer(final ObjectMapper objectMapper, final KafkaTemplate<String, String> kafkaTemplate) {
        super(objectMapper, kafkaTemplate);
    }

    @Override
    String getTopic() {
        return "example-topic";
    }
}
