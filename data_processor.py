import pandas as pd
from datetime import datetime
from cost_calculator import EnterpriseCostCalculator
import json

class DataProcessor:
    def __init__(self, db_manager):
        self.db = db_manager
        self.cost_calc = EnterpriseCostCalculator()

    def normalize_openai_data(self, df, filename):
        """Normalizes OpenAI data structure."""
        records = []
        pricing = self.cost_calc.get_pricing_info('OpenAI')
        monthly_cost = pricing['license_cost_per_user_monthly']

        for _, row in df.iterrows():
            # Basic validation
            if pd.isna(row.get('email')): continue

            # Determine Date (handling weekly vs monthly logic simplistically here)
            # In production, robust date parsing logic from original code goes here
            date_val = pd.to_datetime(row.get('period_start', datetime.now())).strftime('%Y-%m-%d')
            
            base_record = {
                'user_id': row.get('email'),
                'user_name': row.get('name', 'Unknown'),
                'email': row.get('email'),
                'department': self._clean_dept(row.get('department')),
                'date': date_val,
                'tool_source': 'ChatGPT',
                'file_source': filename,
                'cost_usd': monthly_cost # Apply monthly cost to the main record
            }

            # 1. ChatGPT Messages
            if row.get('messages', 0) > 0:
                r = base_record.copy()
                r.update({'feature_used': 'ChatGPT Messages', 'usage_count': row['messages']})
                records.append(r)

            # 2. Tool Messages (Cost usually included in license, so 0 extra)
            if row.get('tool_messages', 0) > 0:
                r = base_record.copy()
                r.update({'feature_used': 'Tool Messages', 'usage_count': row['tool_messages'], 'cost_usd': 0})
                records.append(r)

        return pd.DataFrame(records)

    def _clean_dept(self, dept_str):
        """Parses messy JSON array strings for departments."""
        if pd.isna(dept_str): return 'Unknown'
        try:
            # Handle ["Finance"] format
            if isinstance(dept_str, str) and dept_str.startswith('['):
                import json
                arr = json.loads(dept_str.replace("'", '"'))
                return arr[0].title() if arr else 'Unknown'
            return str(dept_str).title()
        except:
            return str(dept_str).title()

    def process_upload(self, df, filename, tool_type):
        """
        Main entry point. Uses ATOMIC TRANSACTIONS to prevent data loss.
        """
        # 1. Normalize
        if tool_type == 'ChatGPT':
            normalized_df = self.normalize_openai_data(df, filename)
        # ... Add BlueFlame logic here
        else:
            return False, "Unsupported Tool"

        if normalized_df.empty:
            return False, "No valid records found."

        # 2. Prepare SQL Operations
        operations = []
        
        # Step A: Delete existing data for this specific file to avoid duplicates
        operations.append(("DELETE FROM usage_metrics WHERE file_source = ?", (filename,)))
        
        # Step B: Insert new data
        insert_sql = """
            INSERT INTO usage_metrics 
            (user_id, user_name, email, department, date, feature_used, usage_count, cost_usd, tool_source, file_source)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        for _, row in normalized_df.iterrows():
            params = (
                row['user_id'], row['user_name'], row['email'], row['department'],
                row['date'], row['feature_used'], int(row['usage_count']), 
                float(row['cost_usd']), row['tool_source'], row['file_source']
            )
            operations.append((insert_sql, params))

        # 3. Execute Atomically
        try:
            self.db.execute_transaction(operations)
            return True, f"Successfully processed {len(normalized_df)} records."
        except Exception as e:
            return False, f"Database error: {str(e)}"
