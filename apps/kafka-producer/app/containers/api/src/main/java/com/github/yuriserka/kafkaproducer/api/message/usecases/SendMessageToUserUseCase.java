package com.github.yuriserka.kafkaproducer.api.message.usecases;

import org.springframework.stereotype.Component;

import com.github.yuriserka.kafkaproducer.core.gateways.database.outboxevent.OutboxEventDatabaseAdapter;
import com.github.yuriserka.kafkaproducer.core.gateways.outbox.EventTypes;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;

@Component
@RequiredArgsConstructor
@Slf4j
public class SendMessageToUserUseCase {
    private final OutboxEventDatabaseAdapter outboxEventDatabaseAdapter;

    public void execute(final String userId, final String username) {
        log.info("Sending message to user {} aka {}", userId, username);
        outboxEventDatabaseAdapter.saveFromEventType(EventTypes.SEND_MESSAGE_TO_USER, userId, username);
    }
}
