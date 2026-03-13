import asyncio
from unittest.mock import MagicMock, patch
from uuid import uuid4
from decimal import Decimal
from app.core.database import init_db, get_session
from app.models import BillSubmission, BillStatus, MasterPrice, Decision, AuditLog
from app.services.orchestrator import orchestrator
from app.services.ocr import OCRService, LineItemResponse
from app.services.llm import LLMService, MappingResult
from sqlmodel import Session, select, create_engine
from app.core.config import settings

# Override DB to use in-memory SQLite for testing or just use the dev DB
# For this verification, we'll use the dev DB defined in config (PostgreSQL)
# assuming docker-compose is up. If not, we might fail.
# Let's use SQLite for safety and speed in verification.
TEST_DB_URL = "sqlite:///./test.db"
engine = create_engine(TEST_DB_URL)

# Patch the engine in orchestrator and database module
with patch("app.core.database.engine", engine), \
     patch("app.services.orchestrator.engine", engine):

    def setup():
        init_db()
        with Session(engine) as session:
            # Seed Master Price
            session.add(MasterPrice(procedure_code="XRAY_CHEST", procedure_name="Chest X-Ray", standard_unit_price=50.00, allowed_variance_percent=10.0))
            session.commit()

    async def run_verification():
        setup()
        
        # Mock OCR
        mock_ocr = MagicMock(spec=OCRService)
        mock_ocr.extract_text.return_value = "Chest X-Ray 55.00"
        mock_ocr.parse_line_items.return_value = [
            LineItemResponse(
                raw_ocr_text="Chest X-Ray",
                extracted_price=Decimal("55.00"),
                quantity=1,
                mapped_procedure_code=None,
                mapping_confidence=0.0,
                variance_percent=None,
                line_decision=None
            )
        ]
        
        # Mock LLM
        mock_llm = MagicMock(spec=LLMService)
        mock_llm.map_procedure.return_value = MappingResult(
            procedure_code="XRAY_CHEST",
            confidence=0.95,
            reason="Exact match"
        )
        
        # Patch Services
        with patch("app.services.orchestrator.ocr_service", mock_ocr), \
             patch("app.services.orchestrator.llm_service", mock_llm):
            
            # Create Bill
            bill_id = uuid4()
            with Session(engine) as session:
                bill = BillSubmission(id=bill_id, filename="test_bill.pdf", status=BillStatus.PENDING)
                session.add(bill)
                session.commit()
            
            print(f"Created Bill: {bill_id}")
            
            # Run Orchestrator
            await orchestrator.process_bill(bill_id)
            
            # Verify Results
            with Session(engine) as session:
                updated_bill = session.get(BillSubmission, bill_id)
                print(f"Bill Status: {updated_bill.status}")
                print(f"Final Decision: {updated_bill.final_decision}")
                
                line_items = updated_bill.line_items
                for item in line_items:
                    print(f"Line Item: {item.raw_ocr_text} -> {item.mapped_procedure_code}")
                    print(f"Price: {item.extracted_price}, Variance: {item.variance_percent}%")
                    print(f"Decision: {item.line_decision}")
                    
                    # Verification Logic
                    # Standard: 50, Extracted: 55. Variance: (5/50)*100 = 10%.
                    # Allowed: 10%. So 10% <= 10% -> VALID.
                    assert item.line_decision == Decision.VALID
                    assert item.variance_percent == 10.0
                
                audit_logs = updated_bill.audit_logs
                print(f"Audit Logs: {len(audit_logs)}")
                for log in audit_logs:
                    print(f" - {log.component}: {log.current_hash[:10]}...")
                
                assert len(audit_logs) >= 4 # Start, OCR, LLM, Validator, End...
                assert updated_bill.final_decision == Decision.VALID

    if __name__ == "__main__":
        asyncio.run(run_verification())
