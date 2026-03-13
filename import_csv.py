import csv
from decimal import Decimal
from datetime import datetime
from sqlmodel import Session, select
from app.core.database import engine, init_db
from app.models import MasterPrice

CSV_FILE = "Item Master & stock with Tax (1).csv"

def parse_decimal(value):
    if not value or value.strip() == "":
        return Decimal(0)
    try:
        return Decimal(value.strip())
    except:
        return Decimal(0)

def parse_date(value):
    if not value or value.strip() == "":
        return None
    try:
        # Format in CSV seems to be "2025-12-31 00:00:00"
        return datetime.strptime(value.strip(), "%Y-%m-%d %H:%M:%S")
    except:
        return None

def import_csv():
    # Re-init DB to apply schema changes (this doesn't drop tables automatically in SQLModel usually, 
    # but since we are using SQLite and I'll delete the file, it's fine)
    init_db()
    
    with Session(engine) as session:
        with open(CSV_FILE, mode='r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            count = 0
            for row in reader:
                try:
                    item = MasterPrice(
                        procedure_code=row.get('item_code', '').strip(),
                        procedure_name=row.get('item_desc', '').strip(),
                        location_code=row.get('location_code', '').strip(),
                        category=row.get('category', '').strip(),
                        subcategory=row.get('subcategory', '').strip(),
                        batch_no=row.get('batch_no', '').strip(),
                        expiry_date=parse_date(row.get('expiry_date')),
                        cost=parse_decimal(row.get('cost')),
                        standard_unit_price=parse_decimal(row.get('selling_price')),
                        mrp=parse_decimal(row.get('mrp')),
                        stock=parse_decimal(row.get('stock')),
                        tax=parse_decimal(row.get('tax')),
                        tax_amount=parse_decimal(row.get('tax_amount')),
                        
                        allowed_variance_percent=Decimal(10.0),
                        hospital_type=row.get('type', '').strip(),
                        region=row.get('location_name', '').strip(),
                        is_active=True
                    )
                    session.add(item)
                    count += 1
                    
                    if count % 100 == 0:
                        print(f"Processed {count} rows...")
                        
                except Exception as e:
                    print(f"Error processing row {row}: {e}")
            
            session.commit()
            print(f"Successfully imported {count} items.")

if __name__ == "__main__":
    import_csv()
