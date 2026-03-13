from sqlmodel import Session, select
from app.core.database import engine
from app.api.ingestion import get_bill_status
from app.models import BillSubmission

def debug_api():
    with Session(engine) as session:
        # Get a valid bill ID first
        bill = session.exec(select(BillSubmission).limit(1)).first()
        if not bill:
            print("No bills in DB to test.")
            return

        print(f"Testing with Bill ID: {bill.id}")
        
        try:
            # Call the function logic directly (mocking dependency injection)
            response = get_bill_status(str(bill.id), session)
            print("API Call Successful!")
            print(f"Response has {len(response.line_items)} items")
            if response.line_items:
                print(f"Sample item is_payable: {response.line_items[0].get('is_payable')}")
        except Exception as e:
            print(f"API Call Failed: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    debug_api()
