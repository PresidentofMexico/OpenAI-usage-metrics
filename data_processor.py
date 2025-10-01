"""
Data Processor for Multi-Tool AI Usage Metrics

Processes and normalizes AI usage data from multiple sources:
- OpenAI ChatGPT Enterprise
- BlueFlame AI
- Other AI tools (extensible)
"""
import pandas as pd
import sqlite3
from datetime import datetime
import re
import json

class DataProcessor:
    def __init__(self, db_manager):
        self.db = db_manager
    
    def process_monthly_data(self, df, filename):
        """
        Process uploaded AI tool data.
        
        This method now accepts either:
        1. Already-normalized data from app.py (has 'tool_source' column)
        2. Raw OpenAI export data (backward compatibility)
        
        Args:
            df: DataFrame with usage data
            filename: Source filename for tracking
            
        Returns:
            tuple: (success: bool, message: str)
        """
        try:
            print(f"Processing {len(df)} rows from {filename}")
            print(f"DataFrame columns: {list(df.columns)}")
            
            # Check if data is already normalized (from new app.py)
            if 'tool_source' in df.columns and 'feature_used' in df.columns:
                print("Data appears to be pre-normalized")
                processed_df = df.copy()
                
                # Ensure all required columns exist
                required_cols = ['user_id', 'user_name', 'email', 'department', 'date', 
                               'feature_used', 'usage_count', 'cost_usd', 'tool_source', 'file_source']
                
                for col in required_cols:
                    if col not in processed_df.columns:
                        if col == 'email':
                            processed_df['email'] = processed_df.get('user_id', 'unknown@company.com')
                        elif col == 'created_at':
                            processed_df['created_at'] = datetime.now().isoformat()
                        else:
                            processed_df[col] = None
                
            else:
                # Process as raw OpenAI data (backward compatibility)
                print("Processing as raw OpenAI export data")
                processed_df = self.clean_openai_data(df, filename)
            
            if processed_df.empty:
                return False, "No valid data found after processing"
            
            print(f"Processed {len(processed_df)} records. Sample:")
            print(processed_df.head(2))
            
            # Insert into database
            conn = sqlite3.connect(self.db.db_path)
            
            # Ensure we only insert columns that exist in the database
            db_columns = ['user_id', 'user_name', 'email', 'department', 'date', 
                         'feature_used', 'usage_count', 'cost_usd', 'tool_source', 
                         'file_source', 'created_at']
            
            # Select only columns that exist in both dataframe and database schema
            cols_to_insert = [col for col in db_columns if col in processed_df.columns]
            df_to_insert = processed_df[cols_to_insert]
            
            # Add created_at if not present
            if 'created_at' not in df_to_insert.columns:
                df_to_insert['created_at'] = datetime.now().isoformat()
            
            df_to_insert.to_sql('usage_metrics', conn, if_exists='append', index=False)
            conn.close()
            
            # Get tool source for message
            tool_source = processed_df['tool_source'].iloc[0] if 'tool_source' in processed_df.columns else 'Unknown'
            
            return True, f"Successfully processed {len(processed_df)} records from {tool_source} ({filename})"
            
        except Exception as e:
            print(f"Error processing data: {str(e)}")
            import traceback
            traceback.print_exc()
            return False, f"Error processing data: {str(e)}"
    
    def clean_openai_data(self, df, filename):
        """
        Clean and normalize OpenAI usage data format.
        
        This maintains backward compatibility with the original OpenAI CSV format.
        """
        try:
            processed_data = []
            
            for _, row in df.iterrows():
                # Skip rows with no messages
                if pd.isna(row.get('messages', 0)) or row.get('messages', 0) == 0:
                    continue
                
                # Extract basic user info
                user_email = row.get('email', row.get('public_id', 'unknown@company.com'))
                user_name = row.get('name', 'Unknown User')
                department = self.extract_department(row.get('department', 'Unknown'))
                
                # Get date - use period_start or first_day_active_in_period
                period_start = row.get('period_start', row.get('first_day_active_in_period', datetime.now().strftime('%Y-%m-%d')))
                
                # Ensure date is in proper format
                try:
                    period_start = pd.to_datetime(period_start).strftime('%Y-%m-%d')
                except:
                    period_start = datetime.now().strftime('%Y-%m-%d')
                
                messages = row.get('messages', 0)
                
                records = []
                
                # ChatGPT Messages (main message count)
                if messages > 0:
                    records.append({
                        'user_id': user_email,
                        'user_name': user_name,
                        'email': user_email,
                        'department': department,
                        'date': period_start,
                        'feature_used': 'ChatGPT Messages',
                        'usage_count': int(messages),
                        'cost_usd': float(messages) * 0.02,
                        'tool_source': 'ChatGPT',
                        'file_source': filename,
                        'created_at': datetime.now().isoformat()
                    })
                
                # GPT Messages (custom GPTs)
                gpt_messages = row.get('gpt_messages', 0)
                if pd.notna(gpt_messages) and gpt_messages > 0:
                    records.append({
                        'user_id': user_email,
                        'user_name': user_name,
                        'email': user_email,
                        'department': department,
                        'date': period_start,
                        'feature_used': 'GPT Messages',
                        'usage_count': int(gpt_messages),
                        'cost_usd': float(gpt_messages) * 0.02,
                        'tool_source': 'ChatGPT',
                        'file_source': filename,
                        'created_at': datetime.now().isoformat()
                    })
                
                # Tool Messages (code interpreter, web browsing, etc.)
                tool_messages = row.get('tool_messages', 0)
                if pd.notna(tool_messages) and tool_messages > 0:
                    records.append({
                        'user_id': user_email,
                        'user_name': user_name,
                        'email': user_email,
                        'department': department,
                        'date': period_start,
                        'feature_used': 'Tool Messages',
                        'usage_count': int(tool_messages),
                        'cost_usd': float(tool_messages) * 0.01,
                        'tool_source': 'ChatGPT',
                        'file_source': filename,
                        'created_at': datetime.now().isoformat()
                    })
                
                # Project Messages (ChatGPT Projects feature)
                project_messages = row.get('project_messages', 0)
                if pd.notna(project_messages) and project_messages > 0:
                    records.append({
                        'user_id': user_email,
                        'user_name': user_name,
                        'email': user_email,
                        'department': department,
                        'date': period_start,
                        'feature_used': 'Project Messages',
                        'usage_count': int(project_messages),
                        'cost_usd': float(project_messages) * 0.015,
                        'tool_source': 'ChatGPT',
                        'file_source': filename,
                        'created_at': datetime.now().isoformat()
                    })
                
                processed_data.extend(records)
            
            return pd.DataFrame(processed_data)
            
        except Exception as e:
            print(f"Error in clean_openai_data: {str(e)}")
            import traceback
            traceback.print_exc()
            return pd.DataFrame()
    
    def extract_department(self, dept_str):
        """
        Extract department from various formats.
        
        Handles:
        - JSON array strings: '["finance"]' or '["analytics","finance"]'
        - Simple strings: 'Finance'
        - Missing/null values
        """
        if pd.isna(dept_str) or dept_str == '':
            return 'Unknown'
        
        # Handle JSON array format like ["finance"] or ["analytics","finance"]
        if isinstance(dept_str, str) and dept_str.startswith('['):
            try:
                # Try parsing as JSON first
                dept_list = json.loads(dept_str.replace("'", '"'))
                if dept_list and len(dept_list) > 0:
                    return str(dept_list[0]).title()
            except:
                # Fallback to regex extraction
                departments = re.findall(r'"([^"]*)"', dept_str)
                if departments:
                    return departments[0].title()
        
        # Handle simple string
        return str(dept_str).title()
    
    def normalize_blueflame_data(self, df, filename):
        """
        Normalize BlueFlame AI data to standard schema.
        
        NOTE: This is a template - adjust column mappings based on actual BlueFlame format.
        
        Args:
            df: Raw BlueFlame export DataFrame
            filename: Source filename
            
        Returns:
            DataFrame with normalized schema
        """
        try:
            processed_data = []
            
            # TODO: Update these column mappings based on actual BlueFlame export format
            # Common possible column names to look for:
            potential_email_cols = ['email', 'user_email', 'Email', 'User Email']
            potential_name_cols = ['name', 'user_name', 'Name', 'User Name']
            potential_dept_cols = ['department', 'Department', 'dept']
            potential_date_cols = ['date', 'Date', 'month', 'Month', 'period']
            potential_usage_cols = ['messages', 'total_messages', 'usage', 'message_count']
            
            # Find which columns actually exist
            email_col = next((col for col in potential_email_cols if col in df.columns), None)
            name_col = next((col for col in potential_name_cols if col in df.columns), None)
            dept_col = next((col for col in potential_dept_cols if col in df.columns), None)
            date_col = next((col for col in potential_date_cols if col in df.columns), None)
            usage_col = next((col for col in potential_usage_cols if col in df.columns), None)
            
            if not email_col or not usage_col:
                print(f"Warning: Could not find required columns in BlueFlame data")
                print(f"Available columns: {df.columns.tolist()}")
                return pd.DataFrame()
            
            for _, row in df.iterrows():
                user_email = row.get(email_col, 'unknown@company.com')
                user_name = row.get(name_col, user_email) if name_col else user_email
                department = row.get(dept_col, 'Unknown') if dept_col else 'Unknown'
                date = row.get(date_col, datetime.now().strftime('%Y-%m-%d')) if date_col else datetime.now().strftime('%Y-%m-%d')
                usage_count = row.get(usage_col, 0)
                
                # Convert date to proper format
                try:
                    date = pd.to_datetime(date).strftime('%Y-%m-%d')
                except:
                    date = datetime.now().strftime('%Y-%m-%d')
                
                if usage_count > 0:
                    processed_data.append({
                        'user_id': user_email,
                        'user_name': user_name,
                        'email': user_email,
                        'department': department,
                        'date': date,
                        'feature_used': 'BlueFlame Messages',
                        'usage_count': int(usage_count),
                        'cost_usd': float(usage_count) * 0.015,  # Adjust pricing as needed
                        'tool_source': 'BlueFlame AI',
                        'file_source': filename,
                        'created_at': datetime.now().isoformat()
                    })
            
            return pd.DataFrame(processed_data)
            
        except Exception as e:
            print(f"Error normalizing BlueFlame data: {str(e)}")
            import traceback
            traceback.print_exc()
            return pd.DataFrame()
    
    def calculate_growth_metrics(self, df):
        """
        Calculate month-over-month growth metrics.
        
        Args:
            df: DataFrame with usage data
            
        Returns:
            DataFrame with growth rates by period
        """
        try:
            if df.empty:
                return pd.DataFrame()
            
            # Extract year-month from date
            df['period'] = pd.to_datetime(df['date']).dt.to_period('M')
            
            # Group by period and calculate totals
            monthly_totals = df.groupby('period')['usage_count'].sum().sort_index()
            
            if len(monthly_totals) < 2:
                return pd.DataFrame()
            
            # Calculate growth rates
            growth_data = []
            for i in range(1, len(monthly_totals)):
                current = monthly_totals.iloc[i]
                previous = monthly_totals.iloc[i-1]
                growth_rate = ((current - previous) / previous * 100) if previous > 0 else 0
                
                growth_data.append({
                    'period': str(monthly_totals.index[i]),
                    'current_usage': current,
                    'previous_usage': previous,
                    'growth_rate': growth_rate,
                    'growth_absolute': current - previous
                })
            
            return pd.DataFrame(growth_data)
            
        except Exception as e:
            print(f"Error calculating growth metrics: {str(e)}")
            return pd.DataFrame()
    
    def calculate_tool_adoption_metrics(self, df):
        """
        Calculate adoption metrics for each tool.
        
        Args:
            df: DataFrame with usage data
            
        Returns:
            DataFrame with adoption metrics by tool
        """
        try:
            if df.empty or 'tool_source' not in df.columns:
                return pd.DataFrame()
            
            # Group by tool and calculate metrics
            tool_metrics = df.groupby('tool_source').agg({
                'user_id': 'nunique',  # Unique users per tool
                'usage_count': 'sum',  # Total usage per tool
                'cost_usd': 'sum'      # Total cost per tool
            }).reset_index()
            
            tool_metrics.columns = ['tool', 'unique_users', 'total_usage', 'total_cost']
            
            # Calculate adoption rates
            total_unique_users = df['user_id'].nunique()
            tool_metrics['adoption_rate'] = (tool_metrics['unique_users'] / total_unique_users * 100).round(2)
            
            # Calculate average usage per user
            tool_metrics['avg_usage_per_user'] = (tool_metrics['total_usage'] / tool_metrics['unique_users']).round(2)
            
            # Calculate average cost per user
            tool_metrics['avg_cost_per_user'] = (tool_metrics['total_cost'] / tool_metrics['unique_users']).round(2)
            
            return tool_metrics.sort_values('total_usage', ascending=False)
            
        except Exception as e:
            print(f"Error calculating tool adoption metrics: {str(e)}")
            return pd.DataFrame()
    
    def identify_power_users(self, df, threshold_percentile=80):
        """
        Identify power users based on usage patterns.
        
        Args:
            df: DataFrame with usage data
            threshold_percentile: Percentile threshold for power user classification
            
        Returns:
            DataFrame with power user information
        """
        try:
            if df.empty:
                return pd.DataFrame()
            
            # Group by user and calculate total usage
            user_usage = df.groupby(['user_id', 'user_name', 'email', 'department']).agg({
                'usage_count': 'sum',
                'cost_usd': 'sum',
                'tool_source': lambda x: ', '.join(sorted(x.unique()))
            }).reset_index()
            
            # Calculate threshold
            threshold = user_usage['usage_count'].quantile(threshold_percentile / 100)
            
            # Identify power users (top percentile OR anyone with 200+ messages)
            power_users = user_usage[
                (user_usage['usage_count'] >= threshold) | 
                (user_usage['usage_count'] >= 200)
            ].sort_values('usage_count', ascending=False)
            
            # Add ranking
            power_users['rank'] = range(1, len(power_users) + 1)
            
            return power_users
            
        except Exception as e:
            print(f"Error identifying power users: {str(e)}")
            return pd.DataFrame()