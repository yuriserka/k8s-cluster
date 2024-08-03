package com.github.yuriserka.kafkaproducer.api.message;

import java.util.concurrent.TimeUnit;

import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

import com.github.yuriserka.kafkaproducer.api.message.usecases.SendMessageToUserUseCase;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import net.datafaker.Faker;

@Component
@Slf4j
@RequiredArgsConstructor
public class SendMessageScheduler {
    private final SendMessageToUserUseCase sendMessageToUserUseCase;
    private final Faker fakerGenerator = new Faker();

    @Scheduled(fixedRate = 60, timeUnit = TimeUnit.SECONDS)
    public void process() {
        final var startTime = System.currentTimeMillis();
        sendMessageToUserUseCase.execute(fakerGenerator.internet().username());
        log.info("Processing took {} ms", System.currentTimeMillis() - startTime);
    }
}
