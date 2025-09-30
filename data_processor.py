"""Data processing functions for Multi-Provider usage metrics."""
import pandas as pd
import sqlite3
from datetime import datetime
import re
import config

class DataProcessor:
    def __init__(self, db_manager):
        self.db = db_manager
    
    def process_monthly_data(self, df, filename, provider='openai'):
        """Process uploaded monthly data for specified provider."""
        try:
            print(f"Processing {len(df)} rows from {filename} for provider: {provider}")
            print(f"Original DataFrame columns: {list(df.columns)}")
            
            # Clean the data based on provider format
            if provider == 'openai':
                processed_df = self.clean_openai_data(df, filename)
            elif provider == 'blueflame':
                processed_df = self.clean_blueflame_data(df, filename)
            elif provider == 'anthropic':
                processed_df = self.clean_anthropic_data(df, filename)
            else:
                return False, f"Unsupported provider: {provider}"
            
            if processed_df.empty:
                return False, "No valid data found after processing"
            
            # Add provider column
            processed_df['provider'] = provider
            
            print(f"Sample processed data:")
            print(processed_df.head())
            
            # Insert into database
            conn = sqlite3.connect(self.db.db_path)
            processed_df.to_sql('usage_metrics', conn, if_exists='append', index=False)
            conn.close()
            
            return True, f"Successfully processed {len(processed_df)} records from {filename}"
            
        except Exception as e:
            print(f"Error processing data: {str(e)}")
            return False, f"Error processing data: {str(e)}"
    
    def clean_openai_data(self, df, filename):
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
                        'file_source': filename
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
                        'file_source': filename
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
                        'file_source': filename
                    })
                
                processed_data.extend(records)
            
            return pd.DataFrame(processed_data)
            
        except Exception as e:
            print(f"Error in clean_openai_data: {str(e)}")
            return pd.DataFrame()
    
    def clean_blueflame_data(self, df, filename):
        """Clean BlueFlame AI usage data format."""
        try:
            provider_config = config.PROVIDERS['blueflame']
            processed_data = []
            
            for _, row in df.iterrows():
                # Extract basic info using BlueFlame column mapping
                user_id = row.get(provider_config['column_mapping']['user_id'], 'unknown_user')
                user_name = row.get(provider_config['column_mapping']['user_name'], 'Unknown User')
                department = row.get(provider_config['column_mapping']['department'], 'Unknown')
                date = row.get(provider_config['column_mapping']['date'], datetime.now().strftime('%Y-%m-%d'))
                
                # Process each usage column
                for col_name, col_config in provider_config['usage_columns'].items():
                    usage_value = row.get(col_name, 0)
                    if pd.notna(usage_value) and usage_value > 0:
                        processed_data.append({
                            'user_id': str(user_id),
                            'user_name': str(user_name),
                            'department': str(department),
                            'date': str(date),
                            'feature_used': col_config['feature'],
                            'usage_count': int(usage_value),
                            'cost_usd': float(usage_value) * col_config['cost_per_unit'],
                            'created_at': datetime.now().isoformat(),
                            'file_source': filename
                        })
            
            return pd.DataFrame(processed_data)
            
        except Exception as e:
            print(f"Error in clean_blueflame_data: {str(e)}")
            return pd.DataFrame()
    
    def clean_anthropic_data(self, df, filename):
        """Clean Anthropic (Claude) usage data format."""
        try:
            provider_config = config.PROVIDERS['anthropic']
            processed_data = []
            
            for _, row in df.iterrows():
                # Extract basic info using Anthropic column mapping
                user_id = row.get(provider_config['column_mapping']['user_id'], 'unknown@company.com')
                user_name = row.get(provider_config['column_mapping']['user_name'], 'Unknown User')
                department = row.get(provider_config['column_mapping']['department'], 'Unknown')
                date = row.get(provider_config['column_mapping']['date'], datetime.now().strftime('%Y-%m-%d'))
                
                # Process each usage column
                for col_name, col_config in provider_config['usage_columns'].items():
                    usage_value = row.get(col_name, 0)
                    if pd.notna(usage_value) and usage_value > 0:
                        processed_data.append({
                            'user_id': str(user_id),
                            'user_name': str(user_name),
                            'department': str(department),
                            'date': str(date),
                            'feature_used': col_config['feature'],
                            'usage_count': int(usage_value),
                            'cost_usd': float(usage_value) * col_config['cost_per_unit'],
                            'created_at': datetime.now().isoformat(),
                            'file_source': filename
                        })
            
            return pd.DataFrame(processed_data)
            
        except Exception as e:
            print(f"Error in clean_anthropic_data: {str(e)}")
            return pd.DataFrame()
    
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