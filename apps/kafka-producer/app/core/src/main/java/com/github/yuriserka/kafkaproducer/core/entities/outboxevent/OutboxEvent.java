package com.github.yuriserka.kafkaproducer.core.entities.outboxevent;

import java.time.LocalDateTime;

import com.fasterxml.jackson.databind.JsonNode;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import lombok.Builder;
import lombok.Data;

@Entity
@Table(name = "outbox_events")
@Data
@Builder
public class OutboxEvent {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "aggregate_id")
    private String aggregateId;

    @Column(name = "event_type")
    private String eventType;

    @Column(name = "message_broker")
    @Enumerated(EnumType.STRING)
    private MessageBrokers messageBroker;

    private String destination;

    @Column(columnDefinition = "jsonb")
    private JsonNode payload;

    private Boolean processed;

    @Column(name = "created_at")
    private LocalDateTime createdAt;

    public void markAsProcessed() {
        this.processed = true;
    }
}
