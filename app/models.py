from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from uuid import UUID, uuid4
from sqlmodel import SQLModel, Field, Relationship
from enum import Enum

class BillStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class Decision(str, Enum):
    VALID = "VALID"
    INVALID = "INVALID"
    REVIEW = "REVIEW"

class MasterPrice(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    procedure_code: str = Field(index=True)
    procedure_name: str
    location_code: Optional[str] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    batch_no: Optional[str] = None
    expiry_date: Optional[datetime] = None
    cost: Decimal = Field(default=0, max_digits=10, decimal_places=2)
    standard_unit_price: Decimal = Field(default=0, max_digits=10, decimal_places=2) # selling_price
    mrp: Decimal = Field(default=0, max_digits=10, decimal_places=2)
    stock: Decimal = Field(default=0, max_digits=10, decimal_places=2)
    tax: Decimal = Field(default=0, max_digits=10, decimal_places=2)
    tax_amount: Decimal = Field(default=0, max_digits=10, decimal_places=2)
    
    allowed_variance_percent: Decimal = Field(default=0, max_digits=5, decimal_places=2)
    hospital_type: Optional[str] = None # type
    region: Optional[str] = None # location_name
    effective_date: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = Field(default=True)
    is_payable: bool = Field(default=True)

class BillSubmission(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    filename: str
    upload_timestamp: datetime = Field(default_factory=datetime.utcnow)
    status: BillStatus = Field(default=BillStatus.PENDING)
    final_decision: Optional[Decision] = None
    
    line_items: List["BillLineItem"] = Relationship(back_populates="bill")
    audit_logs: List["AuditLog"] = Relationship(back_populates="bill")

class BillLineItem(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    bill_id: UUID = Field(foreign_key="billsubmission.id")
    
    raw_ocr_text: str
    extracted_price: Decimal = Field(max_digits=10, decimal_places=2)
    quantity: int = Field(default=1)
    
    mapped_procedure_code: Optional[str] = Field(default=None)
    mapping_confidence: float = Field(default=0.0)
    mapping_reason: Optional[str] = None
    
    variance_percent: Optional[Decimal] = Field(default=None, max_digits=10, decimal_places=2)
    line_decision: Optional[Decision] = None
    
    bill: BillSubmission = Relationship(back_populates="line_items")

class AuditLog(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    bill_id: UUID = Field(foreign_key="billsubmission.id")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    component: str # OCR, LLM, VALIDATOR
    input_data: str # JSON string
    output_data: str # JSON string
    previous_hash: str # For tamper-proofing
    current_hash: str
    
    bill: BillSubmission = Relationship(back_populates="audit_logs")
