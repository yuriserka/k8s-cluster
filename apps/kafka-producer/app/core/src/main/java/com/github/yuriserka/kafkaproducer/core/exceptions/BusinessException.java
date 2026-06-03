package com.github.yuriserka.kafkaproducer.core.exceptions;

public abstract class BusinessException extends RuntimeException {

  protected BusinessException(final String message) {
    super(message);
  }

  protected BusinessException(final String message, final Throwable cause) {
    super(message, cause);
  }
}
