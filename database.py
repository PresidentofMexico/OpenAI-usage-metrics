"""Multi-provider database manager for AI usage metrics."""
import pandas as pd
import sqlite3
import os
from datetime import datetime

class DatabaseManager:
    def __init__(self, db_path="ai_metrics.db"):
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
                provider TEXT DEFAULT 'OpenAI'
            )
        """)
        
        # Add provider column if it doesn't exist (for existing databases)
        try:
            conn.execute("ALTER TABLE usage_metrics ADD COLUMN provider TEXT DEFAULT 'OpenAI'")
        except sqlite3.OperationalError:
            pass  # Column already exists
            
        conn.commit()
        conn.close()
    
    def get_available_providers(self):
        """Get available providers from data."""
        try:
            conn = sqlite3.connect(self.db_path)
            df = pd.read_sql_query("SELECT DISTINCT provider FROM usage_metrics WHERE provider IS NOT NULL ORDER BY provider", conn)
            conn.close()
            if not df.empty:
                return df['provider'].tolist()
            return ['OpenAI']  # Default
        except Exception as e:
            print(f"Error getting providers: {e}")
            return ['OpenAI']
    
    def get_available_months(self, provider=None):
        """Get available months from data for specific provider."""
        try:
            conn = sqlite3.connect(self.db_path)
            query = "SELECT DISTINCT date FROM usage_metrics"
            params = []
            
            if provider:
                query += " WHERE provider = ?"
                params.append(provider)
                
            query += " ORDER BY date"
            df = pd.read_sql_query(query, conn, params=params)
            conn.close()
            if not df.empty:
                return pd.to_datetime(df['date']).dt.date.tolist()
            return []
        except Exception as e:
            print(f"Error getting months: {e}")
            return []
    
    def get_unique_users(self, provider=None):
        """Get unique users for specific provider."""
        try:
            conn = sqlite3.connect(self.db_path)
            query = "SELECT DISTINCT user_name FROM usage_metrics WHERE user_name IS NOT NULL"
            params = []
            
            if provider:
                query += " AND provider = ?"
                params.append(provider)
                
            df = pd.read_sql_query(query, conn, params=params)
            conn.close()
            return df['user_name'].tolist() if not df.empty else []
        except Exception as e:
            print(f"Error getting users: {e}")
            return []
    
    def get_unique_departments(self, provider=None):
        """Get unique departments for specific provider."""
        try:
            conn = sqlite3.connect(self.db_path)
            query = "SELECT DISTINCT department FROM usage_metrics WHERE department IS NOT NULL"
            params = []
            
            if provider:
                query += " AND provider = ?"
                params.append(provider)
                
            df = pd.read_sql_query(query, conn, params=params)
            conn.close()
            return df['department'].tolist() if not df.empty else []
        except Exception as e:
            print(f"Error getting departments: {e}")
            return []
    
    def get_all_data(self, provider=None):
        """Get all data for specific provider."""
        try:
            conn = sqlite3.connect(self.db_path)
            query = "SELECT * FROM usage_metrics"
            params = []
            
            if provider:
                query += " WHERE provider = ?"
                params.append(provider)
                
            query += " ORDER BY date DESC"
            df = pd.read_sql_query(query, conn, params=params)
            conn.close()
            return df
        except Exception as e:
            print(f"Error getting all data: {e}")
            return pd.DataFrame()
    
    def get_filtered_data(self, start_date, end_date, provider=None, users=None, departments=None):
        """Get filtered data for specific provider."""
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
        except Exception as e:
            print(f"Error getting filtered data: {e}")
            return pd.DataFrame()