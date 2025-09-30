"""Data processing functions for AI usage metrics with multi-provider support."""
import pandas as pd
import sqlite3
from datetime import datetime
import re
import config

class DataProcessor:
    def __init__(self, db_manager):
        self.db = db_manager
    
    def process_monthly_data(self, df, filename, provider='OpenAI'):
        """Process uploaded monthly data with provider support."""
        try:
            print(f"Processing {len(df)} rows from {filename} for provider: {provider}")
            print(f"Original DataFrame columns: {list(df.columns)}")
            
            # Route to appropriate processor based on provider
            if provider == 'OpenAI':
                processed_df = self.clean_openai_data(df, filename, provider)
            elif provider == 'BlueFlame AI':
                processed_df = self.clean_blueflame_data(df, filename, provider)
            elif provider == 'Anthropic':
                processed_df = self.clean_anthropic_data(df, filename, provider)
            elif provider == 'Google AI':
                processed_df = self.clean_google_data(df, filename, provider)
            else:
                processed_df = self.clean_custom_data(df, filename, provider)
            
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
                        'cost_usd': float(messages) * config.PROVIDER_CONFIGS['OpenAI']['cost_model']['ChatGPT Messages'],
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
                        'cost_usd': float(tool_messages) * config.PROVIDER_CONFIGS['OpenAI']['cost_model']['Tool Messages'],
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
                        'cost_usd': float(project_messages) * config.PROVIDER_CONFIGS['OpenAI']['cost_model']['Project Messages'],
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
                # Extract user info
                user_id = row.get('user_id', 'unknown')
                user_name = row.get('username', 'Unknown User')
                department = self.extract_department(row.get('team', 'Unknown'))
                date = row.get('date', '2024-01-01')
                
                # Process queries
                queries = row.get('queries', 0)
                if pd.notna(queries) and queries > 0:
                    processed_data.append({
                        'user_id': str(user_id),
                        'user_name': user_name,
                        'department': department,
                        'date': date,
                        'feature_used': 'Queries',
                        'usage_count': int(queries),
                        'cost_usd': float(queries) * config.PROVIDER_CONFIGS['BlueFlame AI']['cost_model']['Queries'],
                        'created_at': datetime.now().isoformat(),
                        'file_source': filename,
                        'provider': provider
                    })
                
                # Process API calls
                api_calls = row.get('api_calls', 0)
                if pd.notna(api_calls) and api_calls > 0:
                    processed_data.append({
                        'user_id': str(user_id),
                        'user_name': user_name,
                        'department': department,
                        'date': date,
                        'feature_used': 'API Calls',
                        'usage_count': int(api_calls),
                        'cost_usd': float(api_calls) * config.PROVIDER_CONFIGS['BlueFlame AI']['cost_model']['API Calls'],
                        'created_at': datetime.now().isoformat(),
                        'file_source': filename,
                        'provider': provider
                    })
            
            return pd.DataFrame(processed_data)
            
        except Exception as e:
            print(f"Error in clean_blueflame_data: {str(e)}")
            return pd.DataFrame()
    
    def clean_anthropic_data(self, df, filename, provider='Anthropic'):
        """Clean Anthropic usage data format."""
        try:
            processed_data = []
            
            for _, row in df.iterrows():
                # Extract user info
                user_email = row.get('email', 'unknown@company.com')
                user_name = row.get('full_name', 'Unknown User')
                department = self.extract_department(row.get('department', 'Unknown'))
                date = row.get('usage_date', '2024-01-01')
                
                # Process Claude messages
                claude_messages = row.get('claude_messages', 0)
                if pd.notna(claude_messages) and claude_messages > 0:
                    processed_data.append({
                        'user_id': user_email,
                        'user_name': user_name,
                        'department': department,
                        'date': date,
                        'feature_used': 'Claude Messages',
                        'usage_count': int(claude_messages),
                        'cost_usd': float(claude_messages) * config.PROVIDER_CONFIGS['Anthropic']['cost_model']['Claude Messages'],
                        'created_at': datetime.now().isoformat(),
                        'file_source': filename,
                        'provider': provider
                    })
                
                # Process API requests
                api_requests = row.get('api_requests', 0)
                if pd.notna(api_requests) and api_requests > 0:
                    processed_data.append({
                        'user_id': user_email,
                        'user_name': user_name,
                        'department': department,
                        'date': date,
                        'feature_used': 'API Requests',
                        'usage_count': int(api_requests),
                        'cost_usd': float(api_requests) * config.PROVIDER_CONFIGS['Anthropic']['cost_model']['API Requests'],
                        'created_at': datetime.now().isoformat(),
                        'file_source': filename,
                        'provider': provider
                    })
            
            return pd.DataFrame(processed_data)
            
        except Exception as e:
            print(f"Error in clean_anthropic_data: {str(e)}")
            return pd.DataFrame()
    
    def clean_google_data(self, df, filename, provider='Google AI'):
        """Clean Google AI usage data format."""
        try:
            processed_data = []
            
            for _, row in df.iterrows():
                # Extract user info
                user_email = row.get('email', 'unknown@company.com')
                user_name = row.get('name', 'Unknown User')
                department = self.extract_department(row.get('department', 'Unknown'))
                date = row.get('date', '2024-01-01')
                
                # Process Gemini requests
                gemini_requests = row.get('gemini_requests', 0)
                if pd.notna(gemini_requests) and gemini_requests > 0:
                    processed_data.append({
                        'user_id': user_email,
                        'user_name': user_name,
                        'department': department,
                        'date': date,
                        'feature_used': 'Gemini Requests',
                        'usage_count': int(gemini_requests),
                        'cost_usd': float(gemini_requests) * config.PROVIDER_CONFIGS['Google AI']['cost_model']['Gemini Requests'],
                        'created_at': datetime.now().isoformat(),
                        'file_source': filename,
                        'provider': provider
                    })
                
                # Process API calls
                api_calls = row.get('api_calls', 0)
                if pd.notna(api_calls) and api_calls > 0:
                    processed_data.append({
                        'user_id': user_email,
                        'user_name': user_name,
                        'department': department,
                        'date': date,
                        'feature_used': 'API Calls',
                        'usage_count': int(api_calls),
                        'cost_usd': float(api_calls) * config.PROVIDER_CONFIGS['Google AI']['cost_model']['API Calls'],
                        'created_at': datetime.now().isoformat(),
                        'file_source': filename,
                        'provider': provider
                    })
            
            return pd.DataFrame(processed_data)
            
        except Exception as e:
            print(f"Error in clean_google_data: {str(e)}")
            return pd.DataFrame()
    
    def clean_custom_data(self, df, filename, provider='Custom'):
        """Clean custom provider usage data format."""
        try:
            processed_data = []
            
            for _, row in df.iterrows():
                # Extract user info with flexible column mapping
                user_id = row.get('user_id', row.get('email', 'unknown'))
                user_name = row.get('user_name', row.get('name', 'Unknown User'))
                department = self.extract_department(row.get('department', row.get('team', 'Unknown')))
                date = row.get('date', row.get('usage_date', '2024-01-01'))
                feature = row.get('feature_used', row.get('feature', 'General'))
                usage_count = row.get('usage_count', row.get('count', 1))
                cost = row.get('cost_usd', row.get('cost', 0))
                
                if pd.notna(usage_count) and usage_count > 0:
                    processed_data.append({
                        'user_id': str(user_id),
                        'user_name': str(user_name),
                        'department': department,
                        'date': str(date),
                        'feature_used': str(feature),
                        'usage_count': int(usage_count),
                        'cost_usd': float(cost) if pd.notna(cost) else 0.0,
                        'created_at': datetime.now().isoformat(),
                        'file_source': filename,
                        'provider': provider
                    })
            
            return pd.DataFrame(processed_data)
            
        except Exception as e:
            print(f"Error in clean_custom_data: {str(e)}")
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