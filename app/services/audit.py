import hashlib
import json
from datetime import datetime
from sqlmodel import Session, select
from app.models import AuditLog
from uuid import UUID

class AuditService:
    def log_event(self, session: Session, bill_id: UUID, component: str, input_data: dict, output_data: dict):
        # 1. Get the last log hash for this bill (or global chain if strict blockchain)
        # For simplicity, we chain per bill or just global. 
        # Let's do per-bill chaining for now to keep it simple, or global for higher security.
        # Global is better for "Audit Logger (Immutable)".
        
        last_log = session.exec(select(AuditLog).order_by(AuditLog.timestamp.desc())).first()
        previous_hash = last_log.current_hash if last_log else "0" * 64
        
        # 2. Prepare data for hashing
        timestamp = datetime.utcnow().isoformat()
        input_json = json.dumps(input_data, sort_keys=True, default=str)
        output_json = json.dumps(output_data, sort_keys=True, default=str)
        
        content_to_hash = f"{bill_id}{timestamp}{component}{input_json}{output_json}{previous_hash}"
        current_hash = hashlib.sha256(content_to_hash.encode()).hexdigest()
        
        # 3. Create Log Entry
        log_entry = AuditLog(
            bill_id=bill_id,
            timestamp=datetime.fromisoformat(timestamp),
            component=component,
            input_data=input_json,
            output_data=output_json,
            previous_hash=previous_hash,
            current_hash=current_hash
        )
        
        session.add(log_entry)
        session.commit()
        return log_entry

audit_service = AuditService()
