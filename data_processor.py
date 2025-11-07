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
from cost_calculator import EnterpriseCostCalculator

class DataProcessor:
    def __init__(self, db_manager):
        self.db = db_manager
        self.cost_calculator = EnterpriseCostCalculator()
    
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
            
            # Get tool source for the data
            tool_source = processed_df['tool_source'].iloc[0] if 'tool_source' in processed_df.columns else 'Unknown'
            
            # UNIVERSAL DATA SUPERSEDING FOR BOTH BlueFlame AND OpenAI
            # This ensures that each new upload fully replaces data for covered months and users
            # Prevents duplicate/inflated message counts from re-uploads
            if tool_source in ['BlueFlame AI', 'ChatGPT'] and 'date' in processed_df.columns:
                # Extract unique months and users from the new data
                processed_df['date'] = pd.to_datetime(processed_df['date'], errors='coerce')
                # Filter out any invalid dates
                processed_df = processed_df.dropna(subset=['date'])
                unique_months = processed_df['date'].dt.to_period('M').unique()
                unique_users = processed_df['user_id'].unique() if 'user_id' in processed_df.columns else []
                
                if len(unique_months) > 0:
                    print(f"{tool_source} data covers {len(unique_months)} month(s): {[str(m) for m in unique_months]}")
                    print(f"{tool_source} data contains {len(unique_users)} unique user(s)")
                    print("Superseding existing data for these months and users...")
                    
                    conn = sqlite3.connect(self.db.db_path)
                    cursor = conn.cursor()
                    
                    # Delete existing data for each (month, user) combination covered in the new upload
                    deleted_total = 0
                    for month_period in unique_months:
                        # Convert period to date range for this month
                        # month_start: first day of the month
                        # month_end: first day of next month (exclusive upper bound)
                        month_start = month_period.to_timestamp()
                        month_end = (month_period + 1).to_timestamp()
                        
                        for user_id in unique_users:
                            # Delete records for this specific (tool, month, user) combination
                            cursor.execute("""
                                DELETE FROM usage_metrics 
                                WHERE tool_source = ? 
                                AND date >= ? AND date < ?
                                AND user_id = ?
                            """, (tool_source, month_start.strftime('%Y-%m-%d'), month_end.strftime('%Y-%m-%d'), user_id))
                            
                            deleted_count = cursor.rowcount
                            if deleted_count > 0:
                                deleted_total += deleted_count
                                print(f"  Deleted {deleted_count} existing record(s) for {month_period}, user {user_id}")
                    
                    conn.commit()
                    conn.close()
                    
                    if deleted_total > 0:
                        print(f"Total records superseded: {deleted_total}")
                    else:
                        print("No existing records found to supersede (first upload for these months/users)")
            
            # Insert into database
            conn = sqlite3.connect(self.db.db_path)
            
            # Ensure we only insert columns that exist in the database
            db_columns = ['user_id', 'user_name', 'email', 'department', 'date', 
                         'feature_used', 'usage_count', 'cost_usd', 'tool_source', 
                         'file_source', 'last_day_active', 'first_day_active_in_period',
                         'last_day_active_in_period', 'created_at']
            
            # Select only columns that exist in both dataframe and database schema
            cols_to_insert = [col for col in db_columns if col in processed_df.columns]
            df_to_insert = processed_df[cols_to_insert]
            
            # Add created_at if not present
            if 'created_at' not in df_to_insert.columns:
                df_to_insert['created_at'] = datetime.now().isoformat()
            
            df_to_insert.to_sql('usage_metrics', conn, if_exists='append', index=False)
            conn.close()
            
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
        Now calculates costs based on enterprise license pricing ($60/user/month)
        rather than per-message pricing.
        
        Preserves actual period_start dates for both weekly and monthly files,
        enabling week-over-week and month-over-month analysis.
        
        Also preserves activity date fields (last_day_active, first_day_active_in_period, 
        last_day_active_in_period) for user engagement tracking.
        """
        try:
            processed_data = []
            
            # Get pricing info for enterprise licenses
            pricing_info = self.cost_calculator.get_pricing_info('ChatGPT')
            monthly_license_cost = pricing_info['license_cost_per_user_monthly']
            
            for _, row in df.iterrows():
                # Skip rows with no messages
                if pd.isna(row.get('messages', 0)) or row.get('messages', 0) == 0:
                    continue
                
                # Extract basic user info
                user_email = row.get('email', row.get('public_id', 'unknown@company.com'))
                user_name = row.get('name', 'Unknown User')
                department = self.extract_department(row.get('department', 'Unknown'))
                
                # Extract activity dates from CSV
                last_day_active = row.get('last_day_active', None)
                first_day_active_in_period = row.get('first_day_active_in_period', None)
                last_day_active_in_period = row.get('last_day_active_in_period', None)
                
                # Convert to string if not null
                last_day_active = str(last_day_active) if pd.notna(last_day_active) else None
                first_day_active_in_period = str(first_day_active_in_period) if pd.notna(first_day_active_in_period) else None
                last_day_active_in_period = str(last_day_active_in_period) if pd.notna(last_day_active_in_period) else None
                
                # Get date - use period_start or first_day_active_in_period
                # If neither exists, use first day of current month as fallback
                period_start = row.get('period_start', row.get('first_day_active_in_period'))
                
                # Preserve actual period_start date - validate and format only
                # This enables week-over-week analysis for weekly files
                parsed_date = pd.to_datetime(period_start, errors='coerce')
                if pd.isna(parsed_date):
                    # If date is invalid or missing, use first day of current month for consistency
                    now = datetime.now()
                    period_start = f"{now.year}-{now.month:02d}-01"
                else:
                    period_start = parsed_date.strftime('%Y-%m-%d')
                
                messages = row.get('messages', 0)
                
                records = []
                
                # ChatGPT Messages (main message count)
                # Cost is now based on enterprise license, not per-message
                if messages > 0:
                    records.append({
                        'user_id': user_email,
                        'user_name': user_name,
                        'email': user_email,
                        'department': department,
                        'date': period_start,
                        'feature_used': 'ChatGPT Messages',
                        'usage_count': int(messages),
                        'cost_usd': monthly_license_cost,  # Enterprise license cost per user per month
                        'tool_source': 'ChatGPT',
                        'file_source': filename,
                        'last_day_active': last_day_active,
                        'first_day_active_in_period': first_day_active_in_period,
                        'last_day_active_in_period': last_day_active_in_period,
                        'created_at': datetime.now().isoformat()
                    })
                
                # GPT Messages (custom GPTs)
                # These are included in the enterprise license, so cost is 0 (already counted above)
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
                        'cost_usd': 0,  # Included in base license
                        'tool_source': 'ChatGPT',
                        'file_source': filename,
                        'last_day_active': last_day_active,
                        'first_day_active_in_period': first_day_active_in_period,
                        'last_day_active_in_period': last_day_active_in_period,
                        'created_at': datetime.now().isoformat()
                    })
                
                # Tool Messages (code interpreter, web browsing, etc.)
                # These are included in the enterprise license
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
                        'cost_usd': 0,  # Included in base license
                        'tool_source': 'ChatGPT',
                        'file_source': filename,
                        'last_day_active': last_day_active,
                        'first_day_active_in_period': first_day_active_in_period,
                        'last_day_active_in_period': last_day_active_in_period,
                        'created_at': datetime.now().isoformat()
                    })
                
                # Project Messages (ChatGPT Projects feature)
                # These are included in the enterprise license
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
                        'cost_usd': 0,  # Included in base license
                        'tool_source': 'ChatGPT',
                        'file_source': filename,
                        'last_day_active': last_day_active,
                        'first_day_active_in_period': first_day_active_in_period,
                        'last_day_active_in_period': last_day_active_in_period,
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
    
    def parse_blueflame_month_column(self, month_col):
        """
        Parse BlueFlame month column to datetime, handling both formats:
        - 'Mon-YY' format (e.g., 'Sep-24')
        - 'YY-Mon' format (e.g., '25-Sep')
        
        Args:
            month_col (str): Column name containing month information
            
        Returns:
            pandas.Timestamp: Parsed datetime if successful, pd.NaT if parsing fails
        """
        # Try Mon-YY format first (original format)
        month_date = pd.to_datetime(month_col, format='%b-%y', errors='coerce')
        if not pd.isna(month_date):
            return month_date
        
        # Try YY-Mon format (new format)
        month_date = pd.to_datetime(month_col, format='%y-%b', errors='coerce')
        if not pd.isna(month_date):
            return month_date
        
        # Both formats failed
        return pd.NaT
    
    def normalize_blueflame_data(self, df, filename):
        """
        Normalize BlueFlame AI data to standard schema.
        
        Handles both aggregate metrics format and user-level data.
        Now calculates costs based on enterprise license pricing ($125/user/month)
        rather than per-message pricing.
        
        Args:
            df: Raw BlueFlame export DataFrame
            filename: Source filename
            
        Returns:
            DataFrame with normalized schema
        """
        try:
            processed_data = []
            
            # Get pricing info for BlueFlame AI enterprise licenses
            pricing_info = self.cost_calculator.get_pricing_info('BlueFlame AI')
            monthly_license_cost = pricing_info['license_cost_per_user_monthly']
            
            # Check if this is the combined format with 'Table' column
            if 'Table' in df.columns:
                # Split the dataframe by table type
                monthly_trends = df[df['Table'] == 'Overall Monthly Trends']
                user_data = df[(df['Table'] == 'Top 20 Users Total') | 
                              (df['Table'] == 'Top 10 Increasing Users') | 
                              (df['Table'] == 'Top 10 Decreasing Users') |
                              (df['Table'] == 'All Users Total') |
                              (df['Table'] == 'All Increasing Users') |
                              (df['Table'] == 'All Decreasing Users')]
                
                # Deduplicate user data - same user may appear in multiple tables
                if not user_data.empty and 'User ID' in user_data.columns:
                    user_data = user_data.drop_duplicates(subset=['User ID'], keep='first')
                
                # Process monthly trends (aggregate metrics)
                if not monthly_trends.empty:
                    # Get month columns (excluding MoM variance columns)
                    month_cols = [col for col in monthly_trends.columns if col not in ['Table', 'Metric', 'User ID'] 
                                 and not col.startswith('MoM Var')]
                    
                    # Process each month that has data
                    for month_col in month_cols:
                        try:
                            # Parse month to a datetime (supports both Mon-YY and YY-Mon formats)
                            month_date = self.parse_blueflame_month_column(month_col)
                            if pd.isna(month_date):
                                continue
                            
                            # Extract values, handling formatting and missing data
                            total_messages_row = monthly_trends[monthly_trends['Metric'] == 'Total Messages']
                            maus_row = monthly_trends[monthly_trends['Metric'] == 'Monthly Active Users (MAUs)']
                            
                            if total_messages_row.empty or maus_row.empty:
                                continue
                            
                            # Get values and clean them
                            total_messages = total_messages_row[month_col].iloc[0]
                            maus = maus_row[month_col].iloc[0]
                            
                            # Handle dash placeholders and formatting
                            if isinstance(total_messages, str):
                                if total_messages in ['–', '-', '—', 'N/A']:
                                    continue
                                total_messages = int(total_messages.replace(',', ''))
                            
                            if isinstance(maus, str):
                                if maus in ['–', '-', '—', 'N/A']:
                                    maus = 0
                                else:
                                    maus = int(maus.replace(',', ''))
                            
                            # Skip months with no meaningful data
                            if pd.isna(total_messages) or total_messages == 0:
                                continue
                            
                            # Create aggregate record for the month - cost is based on MAUs, not messages
                            total_cost = maus * monthly_license_cost if maus > 0 else 0
                            processed_data.append({
                                'user_id': 'blueflame-aggregate',
                                'user_name': 'BlueFlame Aggregate',
                                'email': 'blueflame-metrics@company.com',
                                'department': 'All Departments',
                                'date': month_date.strftime('%Y-%m-%d'),
                                'feature_used': 'BlueFlame Messages',
                                'usage_count': int(total_messages),
                                'cost_usd': total_cost,  # Enterprise license cost based on active users
                                'tool_source': 'BlueFlame AI',
                                'file_source': filename,
                                'created_at': datetime.now().isoformat()
                            })
                            
                            # If we have MAU data, create synthetic user-level records
                            if maus > 0:
                                avg_messages_per_user = total_messages / maus
                                for i in range(maus):
                                    processed_data.append({
                                        'user_id': f'blueflame-user-{i+1}',
                                        'user_name': f'BlueFlame User {i+1}',
                                        'email': f'blueflame-user-{i+1}@company.com',
                                        'department': 'BlueFlame Users',
                                        'date': month_date.strftime('%Y-%m-%d'),
                                        'feature_used': 'BlueFlame Messages',
                                        'usage_count': round(avg_messages_per_user),
                                        'cost_usd': monthly_license_cost,  # Each user pays enterprise license cost
                                        'tool_source': 'BlueFlame AI',
                                        'file_source': filename,
                                        'created_at': datetime.now().isoformat()
                                    })
                        except Exception as e:
                            print(f"Error processing month {month_col}: {str(e)}")
                
                # Process user data (from Top 20 Users, Top 10 Increasing, etc.)
                if not user_data.empty:
                    # Get month columns (excluding MoM variance columns)
                    month_cols = [col for col in user_data.columns if col not in ['Table', 'Metric', 'User ID'] 
                                 and not col.startswith('MoM Var')]
                    
                    # Process each user
                    for _, row in user_data.iterrows():
                        user_email = row['User ID']
                        user_name = user_email.split('@')[0].replace('.', ' ').title()
                        
                        # Process each month for this user
                        for month_col in month_cols:
                            try:
                                # Parse month to a datetime (supports both Mon-YY and YY-Mon formats)
                                month_date = self.parse_blueflame_month_column(month_col)
                                if pd.isna(month_date):
                                    continue
                                
                                # Get message count for this month
                                message_count = row[month_col]
                                
                                # Handle dash placeholders and formatting
                                if isinstance(message_count, str):
                                    if message_count in ['–', '-', '—', 'N/A']:
                                        continue
                                    message_count = int(message_count.replace(',', ''))
                                
                                # Skip months with no meaningful data
                                if pd.isna(message_count) or message_count == 0:
                                    continue
                                
                                # Create user record for this month
                                # Cost is enterprise license per user, not per message
                                processed_data.append({
                                    'user_id': user_email,
                                    'user_name': user_name,
                                    'email': user_email,
                                    'department': 'BlueFlame Users',  # Default department, can be updated later
                                    'date': month_date.strftime('%Y-%m-%d'),
                                    'feature_used': 'BlueFlame Messages',
                                    'usage_count': int(message_count),
                                    'cost_usd': monthly_license_cost,  # Enterprise license cost per user per month
                                    'tool_source': 'BlueFlame AI',
                                    'file_source': filename,
                                    'created_at': datetime.now().isoformat()
                                })
                            except Exception as e:
                                print(f"Error processing month {month_col} for user {user_email}: {str(e)}")
            
            # If we have the wide-format file with User ID column (new format without 'Table' column)
            # Check this before 'Metric' condition since new format has both User ID and Metric columns
            elif 'User ID' in df.columns:
                # Get month columns (excluding MoM variance columns, Rank, Metric, and User ID)
                month_cols = [col for col in df.columns if col not in ['User ID', 'Rank', 'Metric'] 
                             and not col.startswith('MoM Var')]
                
                # Process each user record
                for _, row in df.iterrows():
                    user_email = row['User ID']
                    if pd.isna(user_email) or not user_email:
                        continue
                    
                    user_name = user_email.split('@')[0].replace('.', ' ').title()
                    
                    # Process each month for this user
                    for month_col in month_cols:
                        try:
                            # Parse month to a datetime (supports both Mon-YY and YY-Mon formats)
                            month_date = self.parse_blueflame_month_column(month_col)
                            if pd.isna(month_date):
                                continue
                            
                            # Get message count for this month
                            message_count = row[month_col]
                            
                            # Handle dash placeholders and formatting
                            if isinstance(message_count, str):
                                if message_count in ['–', '-', '—', 'N/A', '']:
                                    continue
                                message_count = int(message_count.replace(',', ''))
                            
                            # Skip months with no meaningful data
                            if pd.isna(message_count) or message_count == 0:
                                continue
                            
                            # Create user record for this month
                            # Cost is enterprise license per user, not per message
                            processed_data.append({
                                'user_id': user_email,
                                'user_name': user_name,
                                'email': user_email,
                                'department': 'BlueFlame Users',  # Default department, can be updated later
                                'date': month_date.strftime('%Y-%m-%d'),
                                'feature_used': 'BlueFlame Messages',
                                'usage_count': int(message_count),
                                'cost_usd': monthly_license_cost,  # Enterprise license cost per user per month
                                'tool_source': 'BlueFlame AI',
                                'file_source': filename,
                                'created_at': datetime.now().isoformat()
                            })
                        
                        except Exception as e:
                            print(f"Error processing month {month_col} for user {user_email}: {str(e)}")
            
            # Check if this is the summary report with 'Metric' column (but no Table or User ID column)
            elif 'Metric' in df.columns and 'User ID' not in df.columns:
                # Get month columns (excluding MoM variance columns)
                month_cols = [col for col in df.columns if col not in ['Metric'] and not col.startswith('MoM Var')]
                
                # Process each month that has data
                for month_col in month_cols:
                    try:
                        # Parse month to a datetime (supports both Mon-YY and YY-Mon formats)
                        month_date = self.parse_blueflame_month_column(month_col)
                        if pd.isna(month_date):
                            continue
                        
                        # Extract values, handling formatting and missing data
                        total_messages_row = df[df['Metric'] == 'Total Messages']
                        maus_row = df[df['Metric'] == 'Monthly Active Users (MAUs)']
                        
                        if total_messages_row.empty or maus_row.empty:
                            continue
                        
                        # Get values and clean them
                        total_messages = total_messages_row[month_col].iloc[0]
                        maus = maus_row[month_col].iloc[0]
                        
                        # Handle dash placeholders and formatting
                        if isinstance(total_messages, str):
                            if total_messages in ['–', '-', '—', 'N/A']:
                                continue
                            total_messages = int(total_messages.replace(',', ''))
                        
                        if isinstance(maus, str):
                            if maus in ['–', '-', '—', 'N/A']:
                                maus = 0
                            else:
                                maus = int(maus.replace(',', ''))
                        
                        # Skip months with no meaningful data
                        if pd.isna(total_messages) or total_messages == 0:
                            continue
                        
                        # Create aggregate record for the month
                        # Cost based on active users with enterprise license pricing
                        total_cost = maus * monthly_license_cost if maus > 0 else 0
                        processed_data.append({
                            'user_id': 'blueflame-aggregate',
                            'user_name': 'BlueFlame Aggregate',
                            'email': 'blueflame-metrics@company.com',
                            'department': 'All Departments',
                            'date': month_date.strftime('%Y-%m-%d'),
                            'feature_used': 'BlueFlame Messages',
                            'usage_count': int(total_messages),
                            'cost_usd': total_cost,  # Enterprise license cost based on active users
                            'tool_source': 'BlueFlame AI',
                            'file_source': filename,
                            'created_at': datetime.now().isoformat()
                        })
                        
                        # If we have MAU data, create synthetic user-level records
                        if maus > 0:
                            avg_messages_per_user = total_messages / maus
                            for i in range(maus):
                                processed_data.append({
                                    'user_id': f'blueflame-user-{i+1}',
                                    'user_name': f'BlueFlame User {i+1}',
                                    'email': f'blueflame-user-{i+1}@company.com',
                                    'department': 'BlueFlame Users',
                                    'date': month_date.strftime('%Y-%m-%d'),
                                    'feature_used': 'BlueFlame Messages',
                                    'usage_count': round(avg_messages_per_user),
                                    'cost_usd': monthly_license_cost,  # Each user pays enterprise license cost
                                    'tool_source': 'BlueFlame AI',
                                    'file_source': filename,
                                    'created_at': datetime.now().isoformat()
                                })
                    
                    except Exception as e:
                        print(f"Error processing month {month_col}: {str(e)}")
            
            # General user-level data format (older BlueFlame format or future formats)
            else:
                # Process each user record
                for idx, row in df.iterrows():
                    user = row.get('User', row.get('Email', f'blueflame-user-{idx}'))
                    email = row.get('Email', f'{user.lower().replace(" ", ".")}@company.com')
                    messages = row.get('Messages', row.get('Usage', 0))
                    date_col = next((col for col in df.columns if 'Date' in col or 'Month' in col), None)
                    
                    if date_col:
                        try:
                            date = pd.to_datetime(row[date_col], errors='coerce')
                            if pd.isna(date):
                                date = datetime.now().strftime('%Y-%m-%d')
                            else:
                                date = date.strftime('%Y-%m-%d')
                        except:
                            date = datetime.now().strftime('%Y-%m-%d')
                    else:
                        date = datetime.now().strftime('%Y-%m-%d')
                    
                    if messages > 0:
                        processed_data.append({
                            'user_id': email,
                            'user_name': user,
                            'email': email,
                            'department': row.get('Department', 'BlueFlame Users'),
                            'date': date,
                            'feature_used': 'BlueFlame Messages',
                            'usage_count': int(messages),
                            'cost_usd': monthly_license_cost,  # Enterprise license cost per user per month
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
    
    def identify_power_users(self, df, threshold_percentile=95):
        """
        Identify power users based on usage patterns.
        
        Args:
            df: DataFrame with usage data
            threshold_percentile: Percentile threshold for power user classification (default: 95 for top 5%)
            
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
            
            # Calculate threshold (top 5% by default)
            threshold = user_usage['usage_count'].quantile(threshold_percentile / 100)
            
            # Identify power users (top 5% by usage)
            power_users = user_usage[
                user_usage['usage_count'] >= threshold
            ].sort_values('usage_count', ascending=False)
            
            # Add ranking
            power_users['rank'] = range(1, len(power_users) + 1)
            
            return power_users
            
        except Exception as e:
            print(f"Error identifying power users: {str(e)}")
            return pd.DataFrame()