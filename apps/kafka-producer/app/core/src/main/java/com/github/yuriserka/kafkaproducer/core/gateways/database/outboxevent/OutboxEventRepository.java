package com.github.yuriserka.kafkaproducer.core.gateways.database.outboxevent;

import java.util.List;

import org.springframework.data.jpa.repository.JpaRepository;

import com.github.yuriserka.kafkaproducer.core.entities.outboxevent.OutboxEvent;

public interface OutboxEventRepository extends JpaRepository<OutboxEvent, Long> {
    List<OutboxEvent> findAllByProcessedFalse();
}
