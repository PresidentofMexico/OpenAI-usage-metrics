"""Data processing functions for AI usage metrics."""
import pandas as pd
import sqlite3
from datetime import datetime
import re
import config

class DataProcessor:
    def __init__(self, db_manager):
        self.db = db_manager
    
    def detect_provider(self, df):
        """Detect which provider the CSV data is from based on columns."""
        columns = set(df.columns)
        
        # Check each provider's signature columns
        for provider, signature_cols in config.PROVIDER_DETECTION.items():
            if all(col in columns for col in signature_cols):
                return provider
        
        # Default to openai if unable to detect
        return 'openai'
    
    def process_monthly_data(self, df, filename):
        """Process uploaded monthly data with provider detection."""
        try:
            print(f"Processing {len(df)} rows from {filename}")
            print(f"Original DataFrame columns: {list(df.columns)}")
            
            # Detect provider
            provider = self.detect_provider(df)
            print(f"Detected provider: {provider}")
            
            # Clean the data based on detected provider
            if provider == 'openai':
                processed_df = self.clean_openai_data(df, filename, provider)
            elif provider == 'blueflame':
                processed_df = self.clean_blueflame_data(df, filename, provider)
            elif provider == 'anthropic':
                processed_df = self.clean_anthropic_data(df, filename, provider)
            elif provider == 'google':
                processed_df = self.clean_google_data(df, filename, provider)
            else:
                processed_df = self.clean_generic_data(df, filename, provider)
            
            if processed_df.empty:
                return False, "No valid data found after processing"
            
            print(f"Sample processed data:")
            print(processed_df.head())
            
            # Insert into database
            conn = sqlite3.connect(self.db.db_path)
            processed_df.to_sql('usage_metrics', conn, if_exists='append', index=False)
            conn.close()
            
            provider_name = config.PROVIDERS.get(provider, {}).get('display_name', provider)
            return True, f"Successfully processed {len(processed_df)} records from {filename} ({provider_name})"
            
        except Exception as e:
            print(f"Error processing data: {str(e)}")
            return False, f"Error processing data: {str(e)}"
    
    def clean_openai_data(self, df, filename, provider='openai'):
        """Clean OpenAI usage data format."""
        try:
            # Create processed dataframe
            processed_data = []
            
            for _, row in df.iterrows():
                # Skip rows where user is not active or has no messages
                if pd.isna(row.get('messages', 0)) or row.get('messages', 0) == 0:
                    continue
                
                # Extract basic info
                user_email = row.get('email', 'unknown@company.com')
                user_name = row.get('name', 'Unknown User')
                department = self.extract_department(row.get('department', 'Unknown'))
                period_start = row.get('period_start', '2025-08-01')
                messages = row.get('messages', 0)
                
                # Create records for different features based on usage
                records = []
                
                # ChatGPT Messages
                if messages > 0:
                    records.append({
                        'user_id': user_email,
                        'user_name': user_name,
                        'department': department,
                        'date': period_start,
                        'feature_used': 'ChatGPT Messages',
                        'usage_count': int(messages),
                        'cost_usd': float(messages) * 0.02,  # Estimated cost
                        'created_at': datetime.now().isoformat(),
                        'file_source': filename,
                        'provider': provider
                    })
                
                # Tool Messages
                tool_messages = row.get('tool_messages', 0)
                if pd.notna(tool_messages) and tool_messages > 0:
                    records.append({
                        'user_id': user_email,
                        'user_name': user_name,
                        'department': department,
                        'date': period_start,
                        'feature_used': 'Tool Messages',
                        'usage_count': int(tool_messages),
                        'cost_usd': float(tool_messages) * 0.01,  # Estimated cost
                        'created_at': datetime.now().isoformat(),
                        'file_source': filename,
                        'provider': provider
                    })
                
                # Project Messages
                project_messages = row.get('project_messages', 0)
                if pd.notna(project_messages) and project_messages > 0:
                    records.append({
                        'user_id': user_email,
                        'user_name': user_name,
                        'department': department,
                        'date': period_start,
                        'feature_used': 'Project Messages',
                        'usage_count': int(project_messages),
                        'cost_usd': float(project_messages) * 0.015,  # Estimated cost
                        'created_at': datetime.now().isoformat(),
                        'file_source': filename,
                        'provider': provider
                    })
                
                processed_data.extend(records)
            
            return pd.DataFrame(processed_data)
            
        except Exception as e:
            print(f"Error in clean_openai_data: {str(e)}")
            return pd.DataFrame()
    
    def clean_blueflame_data(self, df, filename, provider='blueflame'):
        """Clean BlueFlame AI usage data format."""
        try:
            processed_data = []
            schema = config.PROVIDER_SCHEMAS.get(provider, {})
            
            for _, row in df.iterrows():
                # Get user info using schema mapping
                user_id = self._get_field_value(row, schema.get('user_id', ['user_email']))
                user_name = self._get_field_value(row, schema.get('user_name', ['user_name']))
                department = self.extract_department(self._get_field_value(row, schema.get('department', ['team'])))
                date = self._get_field_value(row, schema.get('date', ['date']))
                
                # Process each usage column
                for col, feature_info in schema.get('usage_columns', {}).items():
                    usage = row.get(col, 0)
                    if pd.notna(usage) and usage > 0:
                        # Check if provider supplies actual cost
                        if 'cost_column' in schema and schema['cost_column'] in row:
                            cost = float(row.get(schema['cost_column'], 0))
                        else:
                            cost = float(usage) * feature_info.get('cost_per_unit', 0.01)
                        
                        processed_data.append({
                            'user_id': user_id,
                            'user_name': user_name,
                            'department': department,
                            'date': date,
                            'feature_used': feature_info['feature_name'],
                            'usage_count': int(usage),
                            'cost_usd': cost,
                            'created_at': datetime.now().isoformat(),
                            'file_source': filename,
                            'provider': provider
                        })
            
            return pd.DataFrame(processed_data)
        except Exception as e:
            print(f"Error in clean_blueflame_data: {str(e)}")
            return pd.DataFrame()
    
    def clean_anthropic_data(self, df, filename, provider='anthropic'):
        """Clean Anthropic usage data format."""
        try:
            processed_data = []
            schema = config.PROVIDER_SCHEMAS.get(provider, {})
            
            for _, row in df.iterrows():
                user_id = self._get_field_value(row, schema.get('user_id', ['user_id']))
                user_name = self._get_field_value(row, schema.get('user_name', ['display_name']))
                department = self.extract_department(self._get_field_value(row, schema.get('department', ['organization'])))
                date = self._get_field_value(row, schema.get('date', ['usage_date']))
                
                for col, feature_info in schema.get('usage_columns', {}).items():
                    usage = row.get(col, 0)
                    if pd.notna(usage) and usage > 0:
                        if 'cost_column' in schema and schema['cost_column'] in row:
                            cost = float(row.get(schema['cost_column'], 0))
                        else:
                            cost = float(usage) * feature_info.get('cost_per_unit', 0.03)
                        
                        processed_data.append({
                            'user_id': user_id,
                            'user_name': user_name,
                            'department': department,
                            'date': date,
                            'feature_used': feature_info['feature_name'],
                            'usage_count': int(usage),
                            'cost_usd': cost,
                            'created_at': datetime.now().isoformat(),
                            'file_source': filename,
                            'provider': provider
                        })
            
            return pd.DataFrame(processed_data)
        except Exception as e:
            print(f"Error in clean_anthropic_data: {str(e)}")
            return pd.DataFrame()
    
    def clean_google_data(self, df, filename, provider='google'):
        """Clean Google usage data format."""
        try:
            processed_data = []
            schema = config.PROVIDER_SCHEMAS.get(provider, {})
            
            for _, row in df.iterrows():
                user_id = self._get_field_value(row, schema.get('user_id', ['email']))
                user_name = self._get_field_value(row, schema.get('user_name', ['full_name']))
                department = self.extract_department(self._get_field_value(row, schema.get('department', ['dept'])))
                date = self._get_field_value(row, schema.get('date', ['report_date']))
                
                for col, feature_info in schema.get('usage_columns', {}).items():
                    usage = row.get(col, 0)
                    if pd.notna(usage) and usage > 0:
                        if 'cost_column' in schema and schema['cost_column'] in row:
                            cost = float(row.get(schema['cost_column'], 0))
                        else:
                            cost = float(usage) * feature_info.get('cost_per_unit', 0.02)
                        
                        processed_data.append({
                            'user_id': user_id,
                            'user_name': user_name,
                            'department': department,
                            'date': date,
                            'feature_used': feature_info['feature_name'],
                            'usage_count': int(usage),
                            'cost_usd': cost,
                            'created_at': datetime.now().isoformat(),
                            'file_source': filename,
                            'provider': provider
                        })
            
            return pd.DataFrame(processed_data)
        except Exception as e:
            print(f"Error in clean_google_data: {str(e)}")
            return pd.DataFrame()
    
    def clean_generic_data(self, df, filename, provider='unknown'):
        """Clean generic data format as fallback."""
        return self.clean_openai_data(df, filename, provider)
    
    def _get_field_value(self, row, field_options):
        """Get field value from row using multiple possible field names."""
        for field in field_options:
            if field in row and pd.notna(row[field]):
                return row[field]
        return 'Unknown'
    
    def extract_department(self, dept_str):
        """Extract department from the department string."""
        if pd.isna(dept_str) or dept_str == '':
            return 'Unknown'
        
        # Handle the format like ["finance"] or ["analytics","finance"]
        if isinstance(dept_str, str) and dept_str.startswith('['):
            # Extract text between quotes
            departments = re.findall(r'"([^"]*)"', dept_str)
            if departments:
                return departments[0].title()  # Return first department, capitalize
        
        return str(dept_str).title()
    
    def calculate_growth_metrics(self, df):
        """Calculate growth metrics."""
        try:
            if df.empty:
                return pd.DataFrame()
            
            # Simple growth calculation
            monthly_totals = df.groupby(df['date'].str[:7])['usage_count'].sum()
            
            if len(monthly_totals) < 2:
                return pd.DataFrame()
            
            growth_data = []
            for i in range(1, len(monthly_totals)):
                current = monthly_totals.iloc[i]
                previous = monthly_totals.iloc[i-1]
                growth_rate = ((current - previous) / previous * 100) if previous > 0 else 0
                
                growth_data.append({
                    'period': monthly_totals.index[i],
                    'growth_rate': growth_rate
                })
            
            return pd.DataFrame(growth_data)
            
        except Exception as e:
            return pd.DataFrame()