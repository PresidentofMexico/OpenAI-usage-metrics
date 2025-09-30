"""Data processing functions for multi-provider AI usage metrics."""
import pandas as pd
import sqlite3
from datetime import datetime
import re

class DataProcessor:
    def __init__(self, db_manager):
        self.db = db_manager
        # Provider configurations
        self.provider_configs = {
            'OpenAI': {
                'columns': ['email', 'name', 'department', 'period_start', 'messages', 'tool_messages', 'project_messages'],
                'user_id_col': 'email',
                'user_name_col': 'name',
                'department_col': 'department',
                'date_col': 'period_start'
            },
            'BlueFlame AI': {
                'columns': ['user_email', 'full_name', 'team', 'usage_date', 'total_queries', 'api_calls'],
                'user_id_col': 'user_email',
                'user_name_col': 'full_name', 
                'department_col': 'team',
                'date_col': 'usage_date'
            },
            'Anthropic': {
                'columns': ['email', 'user_name', 'department', 'date', 'messages_sent', 'tokens_used'],
                'user_id_col': 'email',
                'user_name_col': 'user_name',
                'department_col': 'department', 
                'date_col': 'date'
            }
        }
    
    def detect_provider(self, df):
        """Auto-detect provider based on CSV columns."""
        df_columns = set(df.columns.str.lower())
        
        for provider, config in self.provider_configs.items():
            config_columns = set([col.lower() for col in config['columns']])
            # If at least 60% of expected columns match
            if len(df_columns.intersection(config_columns)) / len(config_columns) >= 0.6:
                return provider
                
        return 'OpenAI'  # Default fallback
    
    def process_monthly_data(self, df, filename, provider=None):
        """Process uploaded monthly data with provider detection."""
        try:
            print(f"Processing {len(df)} rows from {filename}")
            print(f"Original DataFrame columns: {list(df.columns)}")
            
            # Auto-detect provider if not specified
            if provider is None:
                provider = self.detect_provider(df)
                print(f"Auto-detected provider: {provider}")
            
            # Process based on provider
            if provider == 'OpenAI':
                processed_df = self.clean_openai_data(df, filename, provider)
            elif provider == 'BlueFlame AI':
                processed_df = self.clean_blueflame_data(df, filename, provider)
            elif provider == 'Anthropic':
                processed_df = self.clean_anthropic_data(df, filename, provider)
            else:
                # Generic processing for unknown providers
                processed_df = self.clean_generic_data(df, filename, provider)
            
            if processed_df.empty:
                return False, "No valid data found after processing"
            
            print(f"Sample processed data:")
            print(processed_df.head())
            
            # Insert into database
            conn = sqlite3.connect(self.db.db_path)
            processed_df.to_sql('usage_metrics', conn, if_exists='append', index=False)
            conn.close()
            
            return True, f"Successfully processed {len(processed_df)} records from {filename} as {provider} data"
            
        except Exception as e:
            print(f"Error processing data: {str(e)}")
            return False, f"Error processing data: {str(e)}"
    
    def clean_openai_data(self, df, filename, provider):
        """Clean OpenAI usage data format."""
        try:
            processed_data = []
            
            for _, row in df.iterrows():
                if pd.isna(row.get('messages', 0)) or row.get('messages', 0) == 0:
                    continue
                
                user_email = row.get('email', 'unknown@company.com')
                user_name = row.get('name', 'Unknown User')
                department = self.extract_department(row.get('department', 'Unknown'))
                period_start = row.get('period_start', datetime.now().strftime('%Y-%m-%d'))
                messages = row.get('messages', 0)
                
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
                        'cost_usd': float(messages) * 0.02,
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
                        'cost_usd': float(tool_messages) * 0.01,
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
                        'cost_usd': float(project_messages) * 0.015,
                        'created_at': datetime.now().isoformat(),
                        'file_source': filename,
                        'provider': provider
                    })
                
                processed_data.extend(records)
            
            return pd.DataFrame(processed_data)
            
        except Exception as e:
            print(f"Error in clean_openai_data: {str(e)}")
            return pd.DataFrame()
    
    def clean_blueflame_data(self, df, filename, provider):
        """Clean BlueFlame AI usage data format."""
        try:
            processed_data = []
            
            for _, row in df.iterrows():
                user_email = row.get('user_email', 'unknown@company.com')
                user_name = row.get('full_name', 'Unknown User')
                department = row.get('team', 'Unknown')
                usage_date = row.get('usage_date', datetime.now().strftime('%Y-%m-%d'))
                
                # BlueFlame AI specific features
                total_queries = row.get('total_queries', 0)
                api_calls = row.get('api_calls', 0)
                
                records = []
                
                if total_queries > 0:
                    records.append({
                        'user_id': user_email,
                        'user_name': user_name,
                        'department': department,
                        'date': usage_date,
                        'feature_used': 'BlueFlame Queries',
                        'usage_count': int(total_queries),
                        'cost_usd': float(total_queries) * 0.03,  # BlueFlame pricing
                        'created_at': datetime.now().isoformat(),
                        'file_source': filename,
                        'provider': provider
                    })
                
                if api_calls > 0:
                    records.append({
                        'user_id': user_email,
                        'user_name': user_name,
                        'department': department,
                        'date': usage_date,
                        'feature_used': 'API Calls',
                        'usage_count': int(api_calls),
                        'cost_usd': float(api_calls) * 0.005,  # API pricing
                        'created_at': datetime.now().isoformat(),
                        'file_source': filename,
                        'provider': provider
                    })
                
                processed_data.extend(records)
            
            return pd.DataFrame(processed_data)
            
        except Exception as e:
            print(f"Error in clean_blueflame_data: {str(e)}")
            return pd.DataFrame()
    
    def clean_anthropic_data(self, df, filename, provider):
        """Clean Anthropic usage data format."""
        try:
            processed_data = []
            
            for _, row in df.iterrows():
                user_email = row.get('email', 'unknown@company.com')
                user_name = row.get('user_name', 'Unknown User')
                department = row.get('department', 'Unknown')
                date = row.get('date', datetime.now().strftime('%Y-%m-%d'))
                
                messages_sent = row.get('messages_sent', 0)
                tokens_used = row.get('tokens_used', 0)
                
                records = []
                
                if messages_sent > 0:
                    records.append({
                        'user_id': user_email,
                        'user_name': user_name,
                        'department': department,
                        'date': date,
                        'feature_used': 'Claude Messages',
                        'usage_count': int(messages_sent),
                        'cost_usd': float(messages_sent) * 0.018,  # Anthropic pricing
                        'created_at': datetime.now().isoformat(),
                        'file_source': filename,
                        'provider': provider
                    })
                
                if tokens_used > 0:
                    records.append({
                        'user_id': user_email,
                        'user_name': user_name,
                        'department': department,
                        'date': date,
                        'feature_used': 'Token Usage',
                        'usage_count': int(tokens_used),
                        'cost_usd': float(tokens_used) * 0.00001,  # Per token pricing
                        'created_at': datetime.now().isoformat(),
                        'file_source': filename,
                        'provider': provider
                    })
                
                processed_data.extend(records)
            
            return pd.DataFrame(processed_data)
            
        except Exception as e:
            print(f"Error in clean_anthropic_data: {str(e)}")
            return pd.DataFrame()
    
    def clean_generic_data(self, df, filename, provider):
        """Generic data cleaning for unknown providers."""
        try:
            processed_data = []
            
            # Try to map common column names
            column_mapping = {
                'user_id': ['email', 'user_email', 'user_id', 'id'],
                'user_name': ['name', 'user_name', 'full_name', 'display_name'],
                'department': ['department', 'team', 'dept', 'division'],
                'date': ['date', 'usage_date', 'timestamp', 'period_start'],
                'usage_count': ['usage_count', 'count', 'messages', 'queries', 'interactions']
            }
            
            # Find best matching columns
            mapped_cols = {}
            for target_col, possible_cols in column_mapping.items():
                for possible_col in possible_cols:
                    if possible_col in df.columns:
                        mapped_cols[target_col] = possible_col
                        break
            
            for _, row in df.iterrows():
                user_id = row.get(mapped_cols.get('user_id'), 'unknown@company.com')
                user_name = row.get(mapped_cols.get('user_name'), 'Unknown User')
                department = row.get(mapped_cols.get('department'), 'Unknown')
                date = row.get(mapped_cols.get('date'), datetime.now().strftime('%Y-%m-%d'))
                usage_count = row.get(mapped_cols.get('usage_count'), 1)
                
                if usage_count > 0:
                    processed_data.append({
                        'user_id': user_id,
                        'user_name': user_name,
                        'department': department,
                        'date': date,
                        'feature_used': f'{provider} Usage',
                        'usage_count': int(usage_count),
                        'cost_usd': float(usage_count) * 0.02,  # Generic pricing
                        'created_at': datetime.now().isoformat(),
                        'file_source': filename,
                        'provider': provider
                    })
            
            return pd.DataFrame(processed_data)
            
        except Exception as e:
            print(f"Error in clean_generic_data: {str(e)}")
            return pd.DataFrame()
    
    def extract_department(self, dept_str):
        """Extract department from the department string."""
        if pd.isna(dept_str) or dept_str == '':
            return 'Unknown'
        
        # Handle the format like ["finance"] or ["analytics","finance"]
        if isinstance(dept_str, str) and dept_str.startswith('['):
            departments = re.findall(r'"([^"]*)"', dept_str)
            if departments:
                return departments[0].title()
        
        return str(dept_str).title()
    
    def calculate_growth_metrics(self, df):
        """Calculate growth metrics."""
        try:
            if df.empty:
                return pd.DataFrame()
            
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