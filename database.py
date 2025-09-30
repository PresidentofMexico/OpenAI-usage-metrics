"""
Database Manager for OpenAI Usage Metrics

Simple, reliable database operations for OpenAI usage data.
"""
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
                file_source TEXT
            )
        """)
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
        except Exception as e:
            print(f"Error getting months: {e}")
            return []
    
    def get_unique_users(self):
        """Get unique users."""
        try:
            conn = sqlite3.connect(self.db_path)
            df = pd.read_sql_query("SELECT DISTINCT user_name FROM usage_metrics WHERE user_name IS NOT NULL", conn)
            conn.close()
            return df['user_name'].tolist() if not df.empty else []
        except Exception as e:
            print(f"Error getting users: {e}")
            return []
    
    def get_unique_departments(self):
        """Get unique departments."""
        try:
            conn = sqlite3.connect(self.db_path)
            df = pd.read_sql_query("SELECT DISTINCT department FROM usage_metrics WHERE department IS NOT NULL", conn)
            conn.close()
            return df['department'].tolist() if not df.empty else []
        except Exception as e:
            print(f"Error getting departments: {e}")
            return []
    
    def get_all_data(self):
        """Get all data."""
        try:
            conn = sqlite3.connect(self.db_path)
            df = pd.read_sql_query("SELECT * FROM usage_metrics ORDER BY date DESC", conn)
            conn.close()
            return df
        except Exception as e:
            print(f"Error getting all data: {e}")
            return pd.DataFrame()
    
    def get_filtered_data(self, start_date, end_date, users=None, departments=None):
        """Get filtered data."""
        try:
            conn = sqlite3.connect(self.db_path)
            query = "SELECT * FROM usage_metrics WHERE date BETWEEN ? AND ?"
            params = [str(start_date), str(end_date)]
            
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
    
    def delete_all_data(self):
        """Delete all data from database."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute("DELETE FROM usage_metrics")
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error deleting data: {e}")
            return False
    
    def delete_by_file(self, file_source):
        """Delete data from a specific file."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute("DELETE FROM usage_metrics WHERE file_source = ?", (file_source,))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error deleting file data: {e}")
            return False