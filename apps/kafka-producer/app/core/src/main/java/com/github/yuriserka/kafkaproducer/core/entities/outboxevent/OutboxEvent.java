package com.github.yuriserka.kafkaproducer.core.entities.outboxevent;

import java.time.LocalDateTime;

import org.hibernate.annotations.CreationTimestamp;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.type.SqlTypes;

import com.fasterxml.jackson.databind.JsonNode;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Entity
@Table(name = "outbox_events")
@AllArgsConstructor
@NoArgsConstructor
@Data
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

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(columnDefinition = "JSONB")    
    private JsonNode payload;

    private Boolean processed;

    @Column(name = "created_at")
    @CreationTimestamp
    private LocalDateTime createdAt;

    public void markAsProcessed() {
        this.processed = true;
    }
}
