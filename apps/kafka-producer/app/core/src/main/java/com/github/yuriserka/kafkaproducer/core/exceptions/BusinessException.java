package com.github.yuriserka.kafkaproducer.core.exceptions;

import lombok.RequiredArgsConstructor;

@RequiredArgsConstructor
public abstract class BusinessException extends RuntimeException {
    final String message;
}
