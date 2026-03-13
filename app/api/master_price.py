from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List
from app.core.database import get_session
from app.models import MasterPrice

router = APIRouter()

@router.post("/master-prices", response_model=MasterPrice)
def create_master_price(price: MasterPrice, session: Session = Depends(get_session)):
    existing = session.get(MasterPrice, price.procedure_code)
    if existing:
        raise HTTPException(status_code=400, detail="Procedure code already exists")
    session.add(price)
    session.commit()
    session.refresh(price)
    return price

@router.get("/master-prices", response_model=List[MasterPrice])
def list_master_prices(session: Session = Depends(get_session)):
    prices = session.exec(select(MasterPrice)).all()
    return prices

@router.get("/master-prices/{code}", response_model=List[MasterPrice])
def get_master_price(code: str, session: Session = Depends(get_session)):
    prices = session.exec(select(MasterPrice).where(MasterPrice.procedure_code == code)).all()
    if not prices:
        raise HTTPException(status_code=404, detail="Price not found")
    return prices

@router.post("/master-prices/seed")
def seed_master_prices(session: Session = Depends(get_session)):
    # Seed some dummy data
    seed_data = [
        MasterPrice(procedure_code="XRAY_CHEST", procedure_name="Chest X-Ray", standard_unit_price=50.00, allowed_variance_percent=10.0),
        MasterPrice(procedure_code="MRI_BRAIN", procedure_name="Brain MRI", standard_unit_price=500.00, allowed_variance_percent=5.0),
        MasterPrice(procedure_code="CONSULT_GEN", procedure_name="General Consultation", standard_unit_price=100.00, allowed_variance_percent=0.0),
        MasterPrice(procedure_code="BLOOD_CBC", procedure_name="Complete Blood Count", standard_unit_price=20.00, allowed_variance_percent=15.0),
    ]
    
    for item in seed_data:
        existing = session.get(MasterPrice, item.procedure_code)
        if not existing:
            session.add(item)
    
    session.commit()
    return {"status": "seeded"}
