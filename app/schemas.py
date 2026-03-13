from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import List, Optional
from app.models import BillStatus, Decision

class BillSubmissionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    filename: str
    upload_timestamp: datetime
    status: BillStatus
    final_decision: Optional[Decision] = None

from decimal import Decimal

class LineItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    raw_ocr_text: str
    extracted_price: Decimal
    quantity: int
    mapped_procedure_code: Optional[str]
    mapping_confidence: float
    variance_percent: Optional[float]
    line_decision: Optional[Decision]
    is_payable: Optional[bool] = None
    price_difference: Optional[Decimal] = None

class AuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    timestamp: datetime
    component: str
    input_data: str
    output_data: str

class BillDetailResponse(BillSubmissionResponse):
    model_config = ConfigDict(from_attributes=True)
    line_items: List[LineItemResponse]
    audit_logs: List[AuditLogResponse] = []
