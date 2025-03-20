package com.github.yuriserka.kafkaproducer.scheduler.jobs;

import java.util.concurrent.TimeUnit;

import org.springframework.context.annotation.Profile;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

import com.github.yuriserka.kafkaproducer.core.gateways.database.outboxevent.OutboxEventDatabaseAdapter;
import com.github.yuriserka.kafkaproducer.core.gateways.outbox.OutboxEventSenderFactory;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;

@Component
@Slf4j
@RequiredArgsConstructor
@Profile("!test")
public class ProcessOutboxScheduler {
    private final OutboxEventDatabaseAdapter outboxEventDatabaseAdapter;
    private final OutboxEventSenderFactory outboxEventSenderFactory;

    @Scheduled(fixedRate = 60, timeUnit = TimeUnit.SECONDS)
    public void process() {
        outboxEventDatabaseAdapter.findAllNonProcessed().forEach(outboxEvent -> {
            log.info("Processing outbox event {}", outboxEvent);
            outboxEventSenderFactory.create(outboxEvent).emit(outboxEvent);
            outboxEvent.markAsProcessed();
            outboxEventDatabaseAdapter.update(outboxEvent);
        });
    }
}