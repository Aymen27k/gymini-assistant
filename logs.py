import uuid, logging
logging.basicConfig(level=logging.INFO)

def log_event(event_type, details, trace_id=None):
    if trace_id is None:
        trace_id = uuid.uuid4()
    logging.info(f"[{trace_id}] {event_type}: {details}")
    return trace_id
