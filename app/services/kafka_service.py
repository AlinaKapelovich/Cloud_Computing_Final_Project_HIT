"""kafka_service.py — publish an event when a prescription is dispensed.

Bonus / FUTURE EXTENSION. Kafka is an event-streaming platform: one system publishes
events and other systems consume them asynchronously. Here we would publish a
"prescription.dispensed" event so downstream systems (analytics, inventory, auditing)
could react.

This is intentionally a documented STUB: unless KAFKA_ENABLED is set and a broker is
configured, we simply log the event to the console (the fallback). No real Kafka
dependency is required to run or defend the project.
"""
import json
import logging

from flask import current_app

log = logging.getLogger(__name__)

DISPENSED_TOPIC = "prescription.dispensed"


def publish_dispensed_event(prescription: dict) -> dict:
    """Publish a dispense event, or log it to the console when Kafka is disabled."""
    event = {
        "type": DISPENSED_TOPIC,
        "prescription_id": prescription.get("id"),
        "patient_national_id": prescription.get("patient_national_id"),
        "source": prescription.get("source"),
    }

    if current_app.config.get("KAFKA_ENABLED") and current_app.config.get("KAFKA_BOOTSTRAP_SERVERS"):
        try:
            # A real implementation would use confluent-kafka / kafka-python here.
            # Kept as a future extension so the core project has no hard Kafka dependency.
            raise NotImplementedError("Real Kafka producer is a planned future extension.")
        except Exception as exc:  # noqa: BLE001 - never break dispensing over an event.
            log.warning("Kafka publish failed (%s). Logging event to console instead.", exc)

    log.info("[KAFKA fallback] %s -> %s", DISPENSED_TOPIC, json.dumps(event))
    return {"published": False, "mode": "console-log", "event": event}
