"""Simple database manager for OpenAI usage metrics."""
import pandas as pd
import sqlite3
import os
from datetime import datetime

class DatabaseManager:
    def __init__(self, db_path="openai_metrics.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the database with required tables."""
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS usage_metrics (
                id INTEGER PRIMARY KEY,
                user_id TEXT,
                user_name TEXT,
                department TEXT,
                date TEXT,
                feature_used TEXT,
                usage_count INTEGER,
                cost_usd REAL,
                created_at TEXT,
                file_source TEXT,
                provider TEXT DEFAULT 'openai'
            )
        """)
        conn.commit()
        
        # Migrate existing data to have provider column if it doesn't exist
        try:
            conn.execute("SELECT provider FROM usage_metrics LIMIT 1")
        except:
            # Column doesn't exist, add it
            conn.execute("ALTER TABLE usage_metrics ADD COLUMN provider TEXT DEFAULT 'openai'")
            conn.commit()
        
        conn.close()
    
    def get_available_months(self):
        """Get available months from data."""
        try:
            conn = sqlite3.connect(self.db_path)
            df = pd.read_sql_query("SELECT DISTINCT date FROM usage_metrics ORDER BY date", conn)
            conn.close()
            if not df.empty:
                return pd.to_datetime(df['date']).dt.date.tolist()
            return []
        except:
            return []
    
    def get_unique_users(self):
        """Get unique users."""
        try:
            conn = sqlite3.connect(self.db_path)
            df = pd.read_sql_query("SELECT DISTINCT user_name FROM usage_metrics WHERE user_name IS NOT NULL", conn)
            conn.close()
            return df['user_name'].tolist() if not df.empty else []
        except:
            return []
    
    def get_unique_departments(self):
        """Get unique departments."""
        try:
            conn = sqlite3.connect(self.db_path)
            df = pd.read_sql_query("SELECT DISTINCT department FROM usage_metrics WHERE department IS NOT NULL", conn)
            conn.close()
            return df['department'].tolist() if not df.empty else []
        except:
            return []
    
    def get_available_providers(self):
        """Get list of available providers in the database."""
        try:
            conn = sqlite3.connect(self.db_path)
            df = pd.read_sql_query("SELECT DISTINCT provider FROM usage_metrics WHERE provider IS NOT NULL ORDER BY provider", conn)
            conn.close()
            return df['provider'].tolist() if not df.empty else []
        except:
            return []
    
    def get_all_data(self):
        """Get all data."""
        try:
            conn = sqlite3.connect(self.db_path)
            df = pd.read_sql_query("SELECT * FROM usage_metrics ORDER BY date DESC", conn)
            conn.close()
            return df
        except:
            return pd.DataFrame()
    
    def get_filtered_data(self, start_date, end_date, users=None, departments=None, provider=None):
        """Get filtered data."""
        try:
            conn = sqlite3.connect(self.db_path)
            query = "SELECT * FROM usage_metrics WHERE date BETWEEN ? AND ?"
            params = [str(start_date), str(end_date)]
            
            if provider:
                query += " AND provider = ?"
                params.append(provider)
            
            if users:
                query += " AND user_name IN ({})".format(','.join(['?' for _ in users]))
                params.extend(users)
            
            if departments:
                query += " AND department IN ({})".format(','.join(['?' for _ in departments]))
                params.extend(departments)
            
            df = pd.read_sql_query(query, conn, params=params)
            conn.close()
            return df
        except:
            return pd.DataFrame()