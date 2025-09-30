"""Data processing functions for multi-provider usage metrics."""
import pandas as pd
import sqlite3
from datetime import datetime
import re
import config

class DataProcessor:
    def __init__(self, db_manager):
        self.db = db_manager
    
    def process_monthly_data(self, df, filename, provider='OpenAI'):
        """Process uploaded monthly data for any provider."""
        try:
            print(f"Processing {len(df)} rows from {filename} for provider: {provider}")
            print(f"Original DataFrame columns: {list(df.columns)}")
            
            # Clean the data based on provider
            if provider == 'OpenAI':
                processed_df = self.clean_openai_data(df, filename, provider)
            elif provider == 'BlueFlame AI':
                processed_df = self.clean_blueflame_data(df, filename, provider)
            elif provider == 'Anthropic':
                processed_df = self.clean_anthropic_data(df, filename, provider)
            else:
                return False, f"Unsupported provider: {provider}"
            
            if processed_df.empty:
                return False, "No valid data found after processing"
            
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
    
    def clean_openai_data(self, df, filename, provider='OpenAI'):
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
    
    def clean_blueflame_data(self, df, filename, provider='BlueFlame AI'):
        """Clean BlueFlame AI usage data format."""
        try:
            processed_data = []
            
            for _, row in df.iterrows():
                # Extract basic info
                user_id = row.get('user_id', 'unknown_user')
                user_name = row.get('full_name', row.get('name', 'Unknown User'))
                department = row.get('team', row.get('department', 'Unknown'))
                date = row.get('date', row.get('usage_date', '2025-01-01'))
                
                records = []
                
                # Chat Interactions
                chat_interactions = row.get('chat_interactions', 0)
                if pd.notna(chat_interactions) and chat_interactions > 0:
                    records.append({
                        'user_id': user_id,
                        'user_name': user_name,
                        'department': department,
                        'date': date,
                        'feature_used': 'Chat Interactions',
                        'usage_count': int(chat_interactions),
                        'cost_usd': float(chat_interactions) * 0.025,
                        'created_at': datetime.now().isoformat(),
                        'file_source': filename,
                        'provider': provider
                    })
                
                # API Calls
                api_calls = row.get('api_calls', 0)
                if pd.notna(api_calls) and api_calls > 0:
                    records.append({
                        'user_id': user_id,
                        'user_name': user_name,
                        'department': department,
                        'date': date,
                        'feature_used': 'API Calls',
                        'usage_count': int(api_calls),
                        'cost_usd': float(api_calls) * 0.015,
                        'created_at': datetime.now().isoformat(),
                        'file_source': filename,
                        'provider': provider
                    })
                
                # Total Tokens
                total_tokens = row.get('total_tokens', 0)
                if pd.notna(total_tokens) and total_tokens > 0:
                    records.append({
                        'user_id': user_id,
                        'user_name': user_name,
                        'department': department,
                        'date': date,
                        'feature_used': 'Total Tokens',
                        'usage_count': int(total_tokens),
                        'cost_usd': float(total_tokens) * 0.00001,
                        'created_at': datetime.now().isoformat(),
                        'file_source': filename,
                        'provider': provider
                    })
                
                processed_data.extend(records)
            
            return pd.DataFrame(processed_data)
            
        except Exception as e:
            print(f"Error in clean_blueflame_data: {str(e)}")
            return pd.DataFrame()
    
    def clean_anthropic_data(self, df, filename, provider='Anthropic'):
        """Clean Anthropic usage data format."""
        try:
            processed_data = []
            
            for _, row in df.iterrows():
                # Extract basic info
                user_email = row.get('user_email', row.get('email', 'unknown@company.com'))
                user_name = row.get('username', row.get('name', 'Unknown User'))
                department = row.get('org_unit', row.get('department', 'Unknown'))
                date = row.get('date', row.get('usage_date', '2025-01-01'))
                
                records = []
                
                # Claude Messages
                claude_messages = row.get('claude_messages', row.get('messages', 0))
                if pd.notna(claude_messages) and claude_messages > 0:
                    records.append({
                        'user_id': user_email,
                        'user_name': user_name,
                        'department': department,
                        'date': date,
                        'feature_used': 'Claude Messages',
                        'usage_count': int(claude_messages),
                        'cost_usd': float(claude_messages) * 0.03,
                        'created_at': datetime.now().isoformat(),
                        'file_source': filename,
                        'provider': provider
                    })
                
                # Tokens Used
                tokens_used = row.get('tokens_used', 0)
                if pd.notna(tokens_used) and tokens_used > 0:
                    records.append({
                        'user_id': user_email,
                        'user_name': user_name,
                        'department': department,
                        'date': date,
                        'feature_used': 'Tokens Used',
                        'usage_count': int(tokens_used),
                        'cost_usd': float(tokens_used) * 0.000015,
                        'created_at': datetime.now().isoformat(),
                        'file_source': filename,
                        'provider': provider
                    })
                
                processed_data.extend(records)
            
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