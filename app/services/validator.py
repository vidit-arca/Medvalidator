from decimal import Decimal
from typing import Optional, Tuple
from sqlmodel import select
from app.models import MasterPrice, Decision

class ValidationResult:
    def __init__(self, decision: Decision, variance_percent: Decimal, standard_price: Decimal):
        self.decision = decision
        self.variance_percent = variance_percent
        self.standard_price = standard_price

class ValidatorService:
    def validate_line_item(self, session, procedure_code: str, extracted_price: Decimal, quantity: int = 1) -> ValidationResult:
        # Fetch master price(s). Since code is not unique, we need a strategy.
        # For now, we'll try to find an exact match on price, or default to the first one found.
        # Ideally, we would filter by hospital/region if available.
        
        prices = session.exec(select(MasterPrice).where(MasterPrice.procedure_code == procedure_code)).all()
        
        if not prices:
            return ValidationResult(Decision.REVIEW, Decimal(0), Decimal(0))
            
        # Strategy: Find the price that gives the lowest variance (benefit of doubt)
        # or just pick the first one.
        # Let's pick the one with closest price to extracted_price to minimize false negatives?
        # Or strictly the first one?
        # Let's use the first one for now, but log if multiple exist.
        
        master_price = prices[0]
        
        # If we want to be smarter:
        # master_price = min(prices, key=lambda p: abs(p.standard_unit_price - extracted_price))

            
        # Ensure extracted_price is Decimal
        extracted_price = Decimal(str(extracted_price))
        # Use MRP for price comparison instead of standard_unit_price
        standard_price = master_price.mrp * quantity
        
        if standard_price == 0:
             return ValidationResult(Decision.REVIEW, Decimal(0), standard_price)

        # Variance calculation: ((ocr_price - standard_price) / standard_price) * 100
        variance = ((extracted_price - standard_price) / standard_price) * 100
        
        # Decision Logic
        allowed_variance = master_price.allowed_variance_percent
        
        # Check if variance is within allowed range (absolute value check might be needed depending on rules, 
        # but usually we care about overcharging. If undercharging, it's usually VALID or REVIEW.
        # The prompt says: variance > allowed_tolerance -> INVALID.
        # Assuming positive variance means overcharging.
        
        if variance == 0:
            decision = Decision.VALID
        elif variance <= allowed_variance:
            decision = Decision.VALID # or ACCEPTABLE, but mapping to VALID for simplicity as per prompt "ACCEPTABLE" implies valid
        else:
            decision = Decision.INVALID
            
        return ValidationResult(decision, variance, standard_price)

validator_service = ValidatorService()
