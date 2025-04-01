CREATE TABLE IF NOT EXISTS outbox_events (
    id BIGSERIAL PRIMARY KEY,
    aggregate_id VARCHAR(255) NOT NULL,
    event_type VARCHAR(255) NOT NULL,
    message_broker VARCHAR(255) NOT NULL,
    destination VARCHAR(255) NOT NULL,
    payload JSONB NOT NULL,
    processed BOOLEAN NOT NULL default FALSE,
    created_at TIMESTAMP NOT NULL default CURRENT_TIMESTAMP
);