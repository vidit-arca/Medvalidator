from sqlmodel import Session, select
from app.models import BillSubmission, BillStatus, BillLineItem, MasterPrice, Decision
# from app.services.ocr import ocr_service (Replaced by LandingOCRService)
from app.services.llm import llm_service, MappingResult
from app.services.validator import validator_service
from app.services.audit import audit_service
from app.services.ner import medicine_ner
from app.core.database import engine
from uuid import UUID
import os

class Orchestrator:
    async def process_bill(self, bill_id: UUID):
        with Session(engine) as session:
            bill = session.get(BillSubmission, bill_id)
            if not bill:
                return

            try:
                # 1. Update Status
                bill.status = BillStatus.PROCESSING
                session.add(bill)
                session.commit()
                
                audit_service.log_event(session, bill_id, "ORCHESTRATOR", {"action": "start_processing"}, {"status": "PROCESSING"})

                # 2. OCR Extraction
                file_path = os.path.join("raw_storage", f"{bill_id}_{bill.filename}")
                # 2. OCR Extraction (Switched to Landing AI)
                from app.services.landing_ocr import landing_ocr_service
                file_path = os.path.join("raw_storage", f"{bill_id}_{bill.filename}")
                raw_text = landing_ocr_service.extract_text(file_path)
                
                # [UPDATED] Use LLM for Extraction instead of Regex
                extracted_items_dicts = await llm_service.extract_items_from_text(raw_text)
                
                audit_service.log_event(session, bill_id, "OCR_LLM", {"file": file_path}, {"extracted_items_count": len(extracted_items_dicts), "raw_items": extracted_items_dicts})

                # 3. Process Line Items
                final_decision = Decision.VALID
                
                # Fetch all candidates once for efficiency (or fetch per item if list is huge)
                # For MVP, fetching all master prices as candidates
                all_prices = session.exec(select(MasterPrice)).all()
                candidates = [{"code": p.procedure_code, "name": p.procedure_name} for p in all_prices]

                for item_dict in extracted_items_dicts:
                    # Create Line Item Record
                    # Handle potential missing keys or bad formats from LLM
                    item_name = item_dict.get("item_name", "Unknown Item")
                    try:
                        price = float(item_dict.get("price", 0))
                    except:
                        price = 0.0
                    try:
                        qty = int(item_dict.get("quantity", 1))
                    except:
                        qty = 1

                    line_item = BillLineItem(
                        bill_id=bill_id,
                        raw_ocr_text=item_name,
                        extracted_price=price,
                        quantity=qty
                    )
                    
                    # 4. Mapping Strategy: Deterministic First -> LLM Fallback
                    
                    # Strategy 1: Exact Match (Case-insensitive)
                    exact_match = next((c for c in candidates if c["name"].lower() == item_name.lower()), None)
                    if exact_match:
                        line_item.mapped_procedure_code = exact_match["code"]
                        line_item.mapping_confidence = 1.0
                        line_item.mapping_reason = "Exact string match"
                        audit_service.log_event(session, bill_id, "MAPPING", {"strategy": "exact", "item": item_name}, {"code": exact_match["code"]})
                        # session.add(line_item) # Removed to allow validation flow
                        # continue # Removed to allow validation flow

                    # Strategy 2: Strong Substring Match
                    # If the item name is fully contained in a candidate name (or vice versa) and shares significant tokens
                    # e.g. "Oleanz 2.5" in "OLEANZ 2.5 TABLET"
                    elif not line_item.mapped_procedure_code: # Only check if not already matched
                        substring_match = None
                        for c in candidates:
                            c_name = c["name"].lower()
                            i_name = item_name.lower()
                            if (i_name in c_name or c_name in i_name) and len(i_name) > 4:
                                # Verify token overlap to avoid "Tab" matching "Tablet" incorrectly
                                i_tokens = set(i_name.split())
                                c_tokens = set(c_name.split())
                                common = i_tokens.intersection(c_tokens)
                                if len(common) >= 2: # At least 2 words match (e.g. "Oleanz", "2.5")
                                    substring_match = c
                                    break
                        
                        if substring_match:
                            line_item.mapped_procedure_code = substring_match["code"]
                            line_item.mapping_confidence = 0.95
                            line_item.mapping_reason = "Strong substring match"
                            audit_service.log_event(session, bill_id, "MAPPING", {"strategy": "substring", "item": item_name}, {"code": substring_match["code"]})

                    # Strategy 3: DB-driven NER (New)
                    if not line_item.mapped_procedure_code:
                        ner_match = medicine_ner.map_item(item_name)
                        if ner_match:
                            line_item.mapped_procedure_code = ner_match["code"]
                            line_item.mapping_confidence = max(0.9, ner_match["score"])
                            line_item.mapping_reason = f"DB-driven NER match ({ner_match['match_type']})"
                            audit_service.log_event(session, bill_id, "MAPPING", {"strategy": "ner", "item": item_name}, {"code": ner_match["code"], "score": ner_match["score"]})

                    # Strategy 4: No LLM Fallback - Mark as Unmapped
                    # If NER and deterministic matching both failed, the item doesn't exist in the DB
                    if not line_item.mapped_procedure_code:
                        line_item.mapped_procedure_code = None
                        line_item.mapping_confidence = 0.0
                        line_item.mapping_reason = "No matching medicine found in database"
                        audit_service.log_event(session, bill_id, "MAPPING", 
                            {"strategy": "unmapped", "item": item_name}, 
                            {"code": None, "reason": "Not found in MasterPrice database"}
                        )

                    # 5. Validation
                    if line_item.mapped_procedure_code:
                        val_result = validator_service.validate_line_item(
                            session,
                            line_item.mapped_procedure_code, 
                            line_item.extracted_price, 
                            line_item.quantity
                        )
                        line_item.variance_percent = val_result.variance_percent
                        line_item.line_decision = val_result.decision
                        
                        audit_service.log_event(session, bill_id, "VALIDATOR", 
                            {"code": line_item.mapped_procedure_code, "price": line_item.extracted_price}, 
                            {"decision": val_result.decision, "variance": val_result.variance_percent}
                        )
                        
                        if val_result.decision == Decision.INVALID:
                            final_decision = Decision.INVALID
                        elif val_result.decision == Decision.REVIEW and final_decision != Decision.INVALID:
                            final_decision = Decision.REVIEW
                    else:
                        line_item.line_decision = Decision.REVIEW
                        final_decision = Decision.REVIEW # Unmapped items need review

                    session.add(line_item)
                
                # 6. Finalize Bill
                bill.final_decision = final_decision
                bill.status = BillStatus.COMPLETED
                session.add(bill)
                session.commit()
                
                audit_service.log_event(session, bill_id, "ORCHESTRATOR", {"action": "complete_processing"}, {"final_decision": final_decision})

            except Exception as e:
                bill.status = BillStatus.FAILED
                session.add(bill)
                session.commit()
                audit_service.log_event(session, bill_id, "ORCHESTRATOR", {"error": str(e)}, {"status": "FAILED"})
                print(f"Error processing bill {bill_id}: {e}")

orchestrator = Orchestrator()
