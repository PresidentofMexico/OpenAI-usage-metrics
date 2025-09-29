"""
Data processing module for OpenAI usage metrics
"""
import pandas as pd
import numpy as np
from datetime import datetime
import config

class DataProcessor:
    def __init__(self, db_manager):
        self.db = db_manager
    
    def process_monthly_data(self, df, filename):
        """Process uploaded monthly data"""
        try:
            # Clean and standardize data
            df_clean = self.clean_data(df)
            
            # Insert into database
            success, message = self.db.insert_batch_data(df_clean, filename)
            return success, message
            
        except Exception as e:
            return False, f"Error processing data: {str(e)}"
    
    def clean_data(self, df):
        """Clean and standardize the data"""
        # Map columns to standard names
        df_clean = df.copy()
        
        # Ensure required columns exist with default values
        required_columns = ['user_id', 'user_name', 'department', 'date', 'feature_used', 'usage_count', 'cost_usd']
        
        for col in required_columns:
            if col not in df_clean.columns:
                if col in config.DEFAULT_VALUES:
                    df_clean[col] = config.DEFAULT_VALUES[col]
                else:
                    df_clean[col] = None
        
        # Clean date format
        if 'date' in df_clean.columns:
            df_clean['date'] = pd.to_datetime(df_clean['date']).dt.strftime('%Y-%m-%d')
        
        # Ensure numeric columns are numeric
        if 'usage_count' in df_clean.columns:
            df_clean['usage_count'] = pd.to_numeric(df_clean['usage_count'], errors='coerce').fillna(1)
        
        if 'cost_usd' in df_clean.columns:
            df_clean['cost_usd'] = pd.to_numeric(df_clean['cost_usd'], errors='coerce').fillna(0.0)
        
        return df_clean[required_columns]
    
    def calculate_growth_metrics(self, data):
        """Calculate growth metrics"""
        try:
            # Group by month
            data['date'] = pd.to_datetime(data['date'])
            monthly_data = data.groupby(data['date'].dt.to_period('M')).agg({
                'usage_count': 'sum',
                'cost_usd': 'sum',
                'user_id': 'nunique'
            }).reset_index()
            
            if len(monthly_data) < 2:
                return pd.DataFrame()
            
            # Calculate growth rates
            monthly_data['usage_growth'] = monthly_data['usage_count'].pct_change() * 100
            monthly_data['cost_growth'] = monthly_data['cost_usd'].pct_change() * 100
            monthly_data['user_growth'] = monthly_data['user_id'].pct_change() * 100
            
            # Create results
            results = []
            for _, row in monthly_data.tail(3).iterrows():
                if not pd.isna(row['usage_growth']):
                    results.append({
                        'period': str(row['date']),
                        'growth_rate': row['usage_growth']
                    })
            
            return pd.DataFrame(results)
            
        except Exception as e:
            return pd.DataFrame()