import shutil
import os
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Depends
from sqlmodel import Session
from app.core.database import get_session
from app.models import BillSubmission, BillStatus
from app.schemas import BillSubmissionResponse, BillDetailResponse
from uuid import uuid4, UUID
from typing import List
from sqlmodel import select

router = APIRouter()

UPLOAD_DIR = "raw_storage"

@router.post("/upload", response_model=BillSubmissionResponse)
async def upload_bill(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None,
    session: Session = Depends(get_session)
):
    # 1. Validate file type (Removed to allow all formats)
    # if file.content_type not in ["application/pdf", "image/jpeg", "image/png"]:
    #     raise HTTPException(status_code=400, detail="Invalid file type. Only PDF, JPEG, PNG allowed.")
    
    # 2. Create DB Entry
    bill_id = uuid4()
    bill = BillSubmission(
        id=bill_id,
        filename=file.filename,
        status=BillStatus.PENDING
    )
    session.add(bill)
    session.commit()
    session.refresh(bill)
    
    # 3. Save file to disk
    file_path = os.path.join(UPLOAD_DIR, f"{bill_id}_{file.filename}")
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # 4. Trigger Background Processing
    from app.services.orchestrator import orchestrator
    background_tasks.add_task(orchestrator.process_bill, bill_id)
    
    return bill

@router.get("/bills", response_model=List[BillSubmissionResponse])
def list_bills(session: Session = Depends(get_session)):
    bills = session.exec(select(BillSubmission).order_by(BillSubmission.upload_timestamp.desc())).all()
    return bills

@router.get("/bills/{bill_id}", response_model=BillDetailResponse)
def get_bill_status(bill_id: str, session: Session = Depends(get_session)):
    try:
        bill_uuid = UUID(bill_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format")
        
    bill = session.get(BillSubmission, bill_uuid)
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")
        
    # Enrich line items with is_payable status from MasterPrice
    # 1. Collect all mapped codes
    mapped_codes = [item.mapped_procedure_code for item in bill.line_items if item.mapped_procedure_code]
    
    # 2. Fetch MasterPrice info for these codes
    from app.models import MasterPrice
    master_data_map = {}
    if mapped_codes:
        prices = session.exec(select(MasterPrice).where(MasterPrice.procedure_code.in_(mapped_codes))).all()
        # Create map with both is_payable and standard_price (mrp)
        # Note: validator uses MRP * quantity. We should probably show difference based on unit price or total?
        # User said "price difference... from original to how much it was charged".
        # Charged is total line price. Original should be Total MRP (MRP * Qty).
        # We need to act smart here. 'prices' might have duplicates, we take first logic as per validator.
        master_data_map = {p.procedure_code: p for p in prices}
        
    # 3. Construct response manually to include the extra field
    # We need to convert SQLModel objects to Pydantic schemas explicitly or use model_validate/dump
    # But since we are modifying a field not in the DB model, we iterate.
    
    response_items = []
    for item in bill.line_items:
        item_dict = item.model_dump()
        master_item = master_data_map.get(item.mapped_procedure_code)
        
        if master_item:
            item_dict['is_payable'] = master_item.is_payable
            
            # Calculate Price Difference
            # Using logic from validator: standard_price = mrp * quantity
            standard_price = master_item.mrp * item.quantity
            extracted_price = item.extracted_price
            
            # Difference = Charged - Original? Or Original - Charged?
            # User said: "how much price difference is there from original to how muhc it was chargred"
            # Usually: Charged - Expected = Difference (Positive means overcharged)
            item_dict['price_difference'] = extracted_price - standard_price
        else:
            item_dict['is_payable'] = None
            item_dict['price_difference'] = None
            
        response_items.append(item_dict)
        
    # Create the response object
    response = BillDetailResponse(
        id=bill.id,
        filename=bill.filename,
        upload_timestamp=bill.upload_timestamp,
        status=bill.status,
        final_decision=bill.final_decision,
        line_items=response_items,
        audit_logs=bill.audit_logs
    )
    
    return response
