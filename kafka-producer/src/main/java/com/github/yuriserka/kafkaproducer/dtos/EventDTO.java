package com.github.yuriserka.kafkaproducer.dtos;

import java.time.LocalDateTime;

public record EventDTO<T>(String id, String type, LocalDateTime timestamp, T data) {
}
