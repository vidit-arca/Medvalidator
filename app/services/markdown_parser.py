import re
import json
from typing import List, Dict

class MarkdownParser:
    
    def _try_split_medicine_names(self, text: str, expected_count: int) -> list:
        # Medicine form keywords that indicate the end of a medicine name
        form_keywords = {
            'TAB', 'TABS', 'CAP', 'CAPS', 'CAPSULE', 'SYRUP', 'SYP',
            'RESP', 'RESPULES', 'INJ', 'INJECTION', 'GEL', 'DROP', 'DROPS',
            'CREAM', 'LOTION', 'OIN', 'OINTMENT', 'AMP', 'AMPOULE',
            'SACHET', 'PATCH'
        }

        words = text.split()
        parts = []
        current = []

        for i, word in enumerate(words):
            current.append(word)
            clean_word = word.strip('.,;:')
            if clean_word.upper() in form_keywords:
                # Look ahead: if next word starts with uppercase (new medicine name), split here
                if i + 1 < len(words) and words[i + 1][0].isupper() and not words[i + 1][0].isdigit():
                    parts.append(' '.join(current))
                    current = []

        if current:
            parts.append(' '.join(current))

        parts = [p.strip() for p in parts if p.strip()]

        if len(parts) == expected_count:
            return parts

        # Fallback: if we found fewer parts than expected, pad with the last part
        if len(parts) < expected_count:
            padded_parts = []
            for i in range(expected_count):
                if i < len(parts):
                    padded_parts.append(parts[i])
                else:
                    padded_parts.append(parts[-1] if parts else text)
            return padded_parts
            
        # Fallback: if we found MORE parts than expected, merge the excess into the last part
        if len(parts) > expected_count:
            merged = parts[:expected_count-1]
            merged.append(' '.join(parts[expected_count-1:]))
            return merged

    def parse_to_json(self, markdown_text: str) -> str:
        """
        Parses a Markdown table into a JSON list of dictionaries, 
        dynamically mapping rows to the table headers.
        """
        lines = markdown_text.split('\n')
        
        # 1. Extract all table rows (lines starting with |), excluding separator lines
        table_lines = [line.strip() for line in lines if line.strip().startswith('|') and not re.match(r'^\|[\s\-\:]+\|', line.strip())]
        
        if not table_lines:
            return "[]"
            
        # 2. Find the header row (the one with the most column names like QTY, AMOUNT, PRODUCT)
        header_row_idx = 0
        max_keywords = 0
        keywords = {'QTY', 'AMOUNT', 'PRODUCT', 'ITEM', 'DESCRIPTION', 'RATE', 'TOTAL', 'PRICE', 'BATCH', 'EXP', 'MRP', 'NET'}
        
        for i, line in enumerate(table_lines):
            cells = [c.strip().upper() for c in line.strip('|').split('|')]
            matches = sum(1 for c in cells if any(k in c for k in keywords))
            if matches > max_keywords:
                max_keywords = matches
                header_row_idx = i
                
        headers = [cell.replace('<br>', ' ').replace('<BR>', ' ').strip() for cell in table_lines[header_row_idx].strip('|').split('|')]
        parsed_rows = []

        # 3. Process all data rows after the header row
        for line in table_lines[header_row_idx+1:]:
            cells = [cell.strip() for cell in line.strip('|').split('|')]
            
            # --- DATA ROW PROCESSING ---
            
            # Check if any cell in this row contains a <br> tag
            if '<br>' not in line.lower():
                # Normal row: just map cells to headers
                row_dict = {}
                for i, header in enumerate(headers):
                    if i < len(cells):
                        row_dict[header] = cells[i]
                if any(v.strip() for v in row_dict.values()): # Only add if not completely empty
                    parsed_rows.append(row_dict)
                continue

            # This row has <br> tags. Determine if it's squashed or word-wrapped.
            split_cells = [cell.split('<br>') for cell in cells]
            num_sub_rows = max(len(parts) for parts in split_cells)
            
            # Squashed rows will typically have multiple quantities or amounts.
            has_multiple_amounts = False
            numeric_keywords = ['QTY', 'AMOUNT', 'TOTAL', 'PRICE', 'RATE', 'NET', 'GROSS', 'PACK', 'BATCH', 'EXP']
            
            for i, header in enumerate(headers):
                if any(kw in header.upper() for kw in numeric_keywords):
                    if i < len(split_cells) and len(split_cells[i]) > 1:
                        has_multiple_amounts = True
                        break

            # Fallback: if we didn't find any known numeric headers, check if MORE THAN ONE column has splits
            if not has_multiple_amounts:
                cells_with_splits = sum(1 for parts in split_cells if len(parts) > 1)
                if cells_with_splits >= 3:
                    has_multiple_amounts = True

            if not has_multiple_amounts:
                # Word-wrapped single item. Flatten.
                flattened_cells = [cell.replace('<br>', ' ').replace('<BR>', ' ') for cell in cells]
                row_dict = {}
                for i, header in enumerate(headers):
                    if i < len(flattened_cells):
                        row_dict[header] = flattened_cells[i]
                if any(v.strip() for v in row_dict.values()):
                    parsed_rows.append(row_dict)
                continue

            # Squashed multi-item row. Expand it!
            expanded_cells = []
            for parts in split_cells:
                if len(parts) == 1 and num_sub_rows > 1:
                    # Try to split concatenated medicine names
                    expanded = self._try_split_medicine_names(parts[0], num_sub_rows)
                    expanded_cells.append(expanded)
                else:
                    expanded_cells.append(parts)

            # Build a new dictionary for each sub-item
            for i in range(num_sub_rows):
                row_dict = {}
                for col_index, header in enumerate(headers):
                    if col_index < len(expanded_cells):
                        parts = expanded_cells[col_index]
                        # If this cell has a value for sub-row i, use it; else repeat last value
                        if i < len(parts):
                            row_dict[header] = parts[i].strip()
                        else:
                            row_dict[header] = parts[-1].strip() if parts else ""
                if any(v.strip() for v in row_dict.values()):
                    parsed_rows.append(row_dict)

        return json.dumps(parsed_rows, indent=2)

markdown_parser = MarkdownParser()
