package com.github.yuriserka.kafkaproducer.core.gateways.database.outboxevent;

import com.github.yuriserka.kafkaproducer.core.entities.outboxevent.OutboxEvent;
import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;

public interface OutboxEventRepository extends JpaRepository<OutboxEvent, Long> {

  List<OutboxEvent> findAllByProcessedFalse();
}
