package com.github.yuriserka.kafkaproducer.api.config;

import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestControllerAdvice;

import lombok.extern.slf4j.Slf4j;

@RestControllerAdvice
@Slf4j
public abstract class CommonRestAdvice {
    @ExceptionHandler(RuntimeException.class)
    @ResponseStatus(HttpStatus.INTERNAL_SERVER_ERROR)
    public ExceptionDto handleRuntimeException(final RuntimeException e) {
        return logAndReturnDto("An unexpected error occurred", e);
    }

    protected ExceptionDto logAndReturnDto(
        final String message,
        final Exception exception
    ) {
        log.error(
            "[{}] An exception occurred with message: {}",
            exception.getClass().getSimpleName(), exception.getMessage()
        );
        return new ExceptionDto(message);
    }
}
