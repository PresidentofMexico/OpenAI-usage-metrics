"""
Generate sample data for testing the dashboard
"""
import pandas as pd
from datetime import datetime, timedelta
import random

# Set random seed for reproducibility
random.seed(42)

# Generate sample OpenAI data
def generate_openai_sample():
    users = [
        ('john.doe@company.com', 'John Doe', 'Engineering'),
        ('jane.smith@company.com', 'Jane Smith', 'Product'),
        ('bob.johnson@company.com', 'Bob Johnson', 'Finance'),
        ('alice.williams@company.com', 'Alice Williams', 'Engineering'),
        ('charlie.brown@company.com', 'Charlie Brown', 'Sales'),
        ('diana.davis@company.com', 'Diana Davis', 'Marketing'),
        ('eva.miller@company.com', 'Eva Miller', 'Finance'),
        ('frank.wilson@company.com', 'Frank Wilson', 'IT'),
        ('grace.moore@company.com', 'Grace Moore', 'HR'),
        ('henry.taylor@company.com', 'Henry Taylor', 'Engineering'),
    ]
    
    # Generate data for 3 months
    base_date = datetime(2024, 9, 1)
    records = []
    
    for month in range(3):
        current_date = base_date + timedelta(days=30 * month)
        
        for email, name, dept in users:
            # Random usage with some power users
            is_power_user = email in ['john.doe@company.com', 'alice.williams@company.com', 'diana.davis@company.com']
            
            chatgpt_msgs = random.randint(50, 500) if is_power_user else random.randint(5, 100)
            tool_msgs = random.randint(10, 100) if is_power_user else random.randint(0, 30)
            project_msgs = random.randint(5, 50) if is_power_user else random.randint(0, 20)
            
            # ChatGPT Messages
            if chatgpt_msgs > 0:
                records.append({
                    'user_id': email,
                    'user_name': name,
                    'email': email,
                    'department': dept,
                    'date': current_date.strftime('%Y-%m-%d'),
                    'feature_used': 'ChatGPT Messages',
                    'usage_count': chatgpt_msgs,
                    'cost_usd': chatgpt_msgs * 0.02,
                    'tool_source': 'ChatGPT',
                    'file_source': 'sample_openai_data.csv',
                    'created_at': datetime.now().isoformat()
                })
            
            # Tool Messages
            if tool_msgs > 0:
                records.append({
                    'user_id': email,
                    'user_name': name,
                    'email': email,
                    'department': dept,
                    'date': current_date.strftime('%Y-%m-%d'),
                    'feature_used': 'Tool Messages',
                    'usage_count': tool_msgs,
                    'cost_usd': tool_msgs * 0.01,
                    'tool_source': 'ChatGPT',
                    'file_source': 'sample_openai_data.csv',
                    'created_at': datetime.now().isoformat()
                })
            
            # Project Messages
            if project_msgs > 0:
                records.append({
                    'user_id': email,
                    'user_name': name,
                    'email': email,
                    'department': dept,
                    'date': current_date.strftime('%Y-%m-%d'),
                    'feature_used': 'Project Messages',
                    'usage_count': project_msgs,
                    'cost_usd': project_msgs * 0.015,
                    'tool_source': 'ChatGPT',
                    'file_source': 'sample_openai_data.csv',
                    'created_at': datetime.now().isoformat()
                })
    
    return pd.DataFrame(records)

# Generate sample BlueFlame data (some users overlap with OpenAI)
def generate_blueflame_sample():
    users = [
        ('john.doe@company.com', 'John Doe'),  # Overlap with OpenAI
        ('alice.williams@company.com', 'Alice Williams'),  # Overlap with OpenAI
        ('sam.garcia@company.com', 'Sam Garcia'),
        ('lisa.martinez@company.com', 'Lisa Martinez'),
        ('tom.rodriguez@company.com', 'Tom Rodriguez'),
    ]
    
    base_date = datetime(2024, 9, 1)
    records = []
    
    for month in range(3):
        current_date = base_date + timedelta(days=30 * month)
        
        for email, name in users:
            messages = random.randint(50, 300)
            
            records.append({
                'user_id': email,
                'user_name': name,
                'email': email,
                'department': 'BlueFlame Users',
                'date': current_date.strftime('%Y-%m-%d'),
                'feature_used': 'BlueFlame Messages',
                'usage_count': messages,
                'cost_usd': messages * 0.015,
                'tool_source': 'BlueFlame AI',
                'file_source': 'sample_blueflame_data.csv',
                'created_at': datetime.now().isoformat()
            })
    
    return pd.DataFrame(records)

if __name__ == "__main__":
    # Generate and combine data
    openai_data = generate_openai_sample()
    blueflame_data = generate_blueflame_sample()
    
    print(f"Generated {len(openai_data)} OpenAI records")
    print(f"Generated {len(blueflame_data)} BlueFlame records")
    
    # Save to database
    import sys
    sys.path.insert(0, '/home/runner/work/OpenAI-usage-metrics/OpenAI-usage-metrics')
    from database import DatabaseManager
    
    db = DatabaseManager()
    
    # Insert data
    combined_data = pd.concat([openai_data, blueflame_data], ignore_index=True)
    
    # Use database insert
    import sqlite3
    conn = sqlite3.connect(db.db_path)
    combined_data.to_sql('usage_metrics', conn, if_exists='replace', index=False)
    conn.close()
    
    print(f"\n✅ Successfully inserted {len(combined_data)} records into database")
    print(f"📊 Unique users: {combined_data['email'].nunique()}")
    print(f"📅 Date range: {combined_data['date'].min()} to {combined_data['date'].max()}")
    print(f"💰 Total cost: ${combined_data['cost_usd'].sum():.2f}")
