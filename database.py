"""Simple database manager for Multi-Provider usage metrics."""
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
        
        # Create the table if it doesn't exist
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
        
        # Check if provider column exists, if not add it (migration)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(usage_metrics)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'provider' not in columns:
            print("Migrating database: Adding provider column...")
            conn.execute("ALTER TABLE usage_metrics ADD COLUMN provider TEXT DEFAULT 'openai'")
            # Update existing records to have 'openai' as provider
            conn.execute("UPDATE usage_metrics SET provider = 'openai' WHERE provider IS NULL")
            print("Migration complete!")
        
        conn.commit()
        conn.close()
    
    def get_available_months(self, provider=None):
        """Get available months from data."""
        try:
            conn = sqlite3.connect(self.db_path)
            query = "SELECT DISTINCT date FROM usage_metrics"
            if provider:
                query += " WHERE provider = ?"
                df = pd.read_sql_query(query + " ORDER BY date", conn, params=[provider])
            else:
                df = pd.read_sql_query(query + " ORDER BY date", conn)
            conn.close()
            if not df.empty:
                return pd.to_datetime(df['date']).dt.date.tolist()
            return []
        except:
            return []
    
    def get_unique_users(self, provider=None):
        """Get unique users."""
        try:
            conn = sqlite3.connect(self.db_path)
            query = "SELECT DISTINCT user_name FROM usage_metrics WHERE user_name IS NOT NULL"
            if provider:
                query += " AND provider = ?"
                df = pd.read_sql_query(query, conn, params=[provider])
            else:
                df = pd.read_sql_query(query, conn)
            conn.close()
            return df['user_name'].tolist() if not df.empty else []
        except:
            return []
    
    def get_unique_departments(self, provider=None):
        """Get unique departments."""
        try:
            conn = sqlite3.connect(self.db_path)
            query = "SELECT DISTINCT department FROM usage_metrics WHERE department IS NOT NULL"
            if provider:
                query += " AND provider = ?"
                df = pd.read_sql_query(query, conn, params=[provider])
            else:
                df = pd.read_sql_query(query, conn)
            conn.close()
            return df['department'].tolist() if not df.empty else []
        except:
            return []
    
    def get_all_data(self, provider=None):
        """Get all data."""
        try:
            conn = sqlite3.connect(self.db_path)
            query = "SELECT * FROM usage_metrics"
            if provider:
                query += " WHERE provider = ?"
                df = pd.read_sql_query(query + " ORDER BY date DESC", conn, params=[provider])
            else:
                df = pd.read_sql_query(query + " ORDER BY date DESC", conn)
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