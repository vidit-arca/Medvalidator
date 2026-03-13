import pandas as pd
from decimal import Decimal
from datetime import datetime
from sqlmodel import Session, select, delete
from app.core.database import engine, init_db
from app.models import MasterPrice

EXCEL_FILE = "Item Master & stock with Tax added payable and non payable items.xlsx"

def parse_decimal(value):
    if pd.isna(value) or value == "":
        return Decimal(0)
    try:
        return Decimal(str(value).strip())
    except:
        return Decimal(0)

def parse_date(value):
    if pd.isna(value) or value == "":
        return None
    try:
        if isinstance(value, datetime):
            return value
        # Basic string parsing if it's not a datetime object
        return datetime.strptime(str(value).strip(), "%Y-%m-%d %H:%M:%S")
    except:
        return None

def import_excel():
    print("Dropping MasterPrice table to update schema...")
    try:
        MasterPrice.__table__.drop(engine)
    except Exception as e:
        print(f"Table might not exist, skipping drop: {e}")

    print("Initializing database...")
    init_db()
    
    with Session(engine) as session:
        print("Clearing existing MasterPrice data...")
        session.exec(delete(MasterPrice))
        
        print(f"Reading {EXCEL_FILE}...")
        df = pd.read_excel(EXCEL_FILE)
        
        # Replace NaN with safe values for string fields if needed, or handle in loop
        df = df.fillna("")
        
        count = 0
        print("Importing rows...")
        for _, row in df.iterrows():
            try:
                # Map Excel columns to MasterPrice model
                # 'item_code' -> procedure_code
                # 'item_desc' -> procedure_name
                
                item = MasterPrice(
                    procedure_code=str(row.get('item_code', '')).strip(),
                    procedure_name=str(row.get('item_desc', '')).strip(),
                    location_code=str(row.get('location_code', '')).strip(),
                    category=str(row.get('category', '')).strip(),
                    subcategory=str(row.get('subcategory', '')).strip(),
                    batch_no=str(row.get('batch_no', '')).strip(),
                    expiry_date=parse_date(row.get('expiry_date')),
                    cost=parse_decimal(row.get('cost')),
                    standard_unit_price=parse_decimal(row.get('selling_price')), # selling_price -> standard_unit_price
                    mrp=parse_decimal(row.get('mrp')),
                    stock=parse_decimal(row.get('stock')),
                    tax=parse_decimal(row.get('tax')),
                    tax_amount=parse_decimal(row.get('tax_amount')),
                    
                    allowed_variance_percent=Decimal(10.0),
                    hospital_type=str(row.get('type', '')).strip(),
                    region=str(row.get('location_name', '')).strip(),
                    is_active=True, # Defaulting to True
                    is_payable=True if 'Payable' in str(row.get('Payable or non-payable items ', '')) else False
                )
                session.add(item)
                count += 1
                
                if count % 100 == 0:
                    print(f"Processed {count} rows...")
                    
            except Exception as e:
                print(f"Error processing row {count}: {e}")
        
        session.commit()
        print(f"Successfully imported {count} items.")

if __name__ == "__main__":
    import_excel()
