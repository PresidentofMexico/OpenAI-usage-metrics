"""
Simple database manager for OpenAI usage metrics
"""
import pandas as pd
import sqlite3
import os
from datetime import datetime

class DatabaseManager:
    def __init__(self, db_path="data/openai_metrics.db"):
        self.db_path = db_path
        # Create data directory if it doesn't exist
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.init_database()
    
    def get_connection(self):
        return sqlite3.connect(self.db_path)
    
    def init_database(self):
        """Initialize database and create tables"""
        with self.get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS usage_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    user_name TEXT,
                    department TEXT,
                    date DATE NOT NULL,
                    feature_used TEXT,
                    usage_count INTEGER DEFAULT 0,
                    cost_usd DECIMAL(10,2) DEFAULT 0.00,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
    
    def insert_batch_data(self, df, file_source):
        """Insert batch data from DataFrame"""
        try:
            with self.get_connection() as conn:
                df.to_sql('usage_metrics', conn, if_exists='append', index=False)
                return True, f"Successfully inserted {len(df)} records"
        except Exception as e:
            return False, f"Error inserting data: {str(e)}"
    
    def get_all_data(self):
        """Get all data"""
        with self.get_connection() as conn:
            return pd.read_sql_query("SELECT * FROM usage_metrics ORDER BY date DESC", conn)
    
    def get_filtered_data(self, start_date, end_date, users=None, departments=None):
        """Get filtered data"""
        query = "SELECT * FROM usage_metrics WHERE date BETWEEN ? AND ?"
        params = [start_date, end_date]
        
        if users:
            query += f" AND user_id IN ({','.join(['?' for _ in users])})"
            params.extend(users)
        
        if departments:
            query += f" AND department IN ({','.join(['?' for _ in departments])})"
            params.extend(departments)
        
        query += " ORDER BY date DESC"
        
        with self.get_connection() as conn:
            return pd.read_sql_query(query, conn, params=params)
    
    def get_available_months(self):
        """Get available months"""
        with self.get_connection() as conn:
            result = conn.execute("SELECT DISTINCT date FROM usage_metrics ORDER BY date").fetchall()
            if result:
                dates = [datetime.strptime(row[0], '%Y-%m-%d').date() for row in result]
                return dates
            return []
    
    def get_unique_users(self):
        """Get unique users"""
        with self.get_connection() as conn:
            result = conn.execute("SELECT DISTINCT user_id FROM usage_metrics ORDER BY user_id").fetchall()
            return [row[0] for row in result]
    
    def get_unique_departments(self):
        """Get unique departments"""
        with self.get_connection() as conn:
            result = conn.execute("SELECT DISTINCT department FROM usage_metrics WHERE department IS NOT NULL ORDER BY department").fetchall()
            return [row[0] for row in result]