"""
Database Manager for Multi-Tool AI Usage Metrics

Handles database operations for OpenAI ChatGPT, BlueFlame AI, and other AI tool usage data.
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
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Create main usage metrics table with new columns for multi-tool support
            conn.execute("""
                CREATE TABLE IF NOT EXISTS usage_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    user_name TEXT,
                    email TEXT,
                    department TEXT,
                    date TEXT NOT NULL,
                    feature_used TEXT,
                    usage_count INTEGER,
                    cost_usd REAL,
                    tool_source TEXT DEFAULT 'ChatGPT',
                    file_source TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
            
            # Check if we need to migrate existing data (add email and tool_source columns)
            # This MUST happen BEFORE creating indexes on these columns
            try:
                cursor = conn.execute("PRAGMA table_info(usage_metrics)")
                columns = [row[1] for row in cursor.fetchall()]
                print(f"Current columns in database: {columns}")
            except Exception as e:
                print(f"Error checking table columns: {e}")
                conn.close()
                raise
            
            # Migrate email column if needed
            if 'email' not in columns:
                try:
                    print("Migrating database: Adding 'email' column...")
                    conn.execute("ALTER TABLE usage_metrics ADD COLUMN email TEXT")
                    # Copy user_id to email for existing records (assuming user_id is email)
                    conn.execute("UPDATE usage_metrics SET email = user_id WHERE email IS NULL")
                    conn.commit()
                except Exception as e:
                    print(f"Error adding email column: {e}")
                    conn.close()
                    raise
            
            # Migrate tool_source column if needed
            if 'tool_source' not in columns:
                try:
                    print("Migrating database: Adding 'tool_source' column...")
                    conn.execute("ALTER TABLE usage_metrics ADD COLUMN tool_source TEXT DEFAULT 'ChatGPT'")
                    # Set all existing records to ChatGPT
                    conn.execute("UPDATE usage_metrics SET tool_source = 'ChatGPT' WHERE tool_source IS NULL")
                    conn.commit()
                except Exception as e:
                    print(f"Error adding tool_source column: {e}")
                    conn.close()
                    raise
            
            # Verify all required columns exist before creating indexes
            try:
                cursor = conn.execute("PRAGMA table_info(usage_metrics)")
                final_columns = [row[1] for row in cursor.fetchall()]
                print(f"Final columns after migration: {final_columns}")
                
                required_columns = ['user_id', 'email', 'tool_source', 'date']
                missing_columns = [col for col in required_columns if col not in final_columns]
                
                if missing_columns:
                    error_msg = f"Required columns missing after migration: {missing_columns}"
                    print(f"ERROR: {error_msg}")
                    conn.close()
                    raise RuntimeError(error_msg)
            except RuntimeError:
                raise
            except Exception as e:
                print(f"Error verifying columns: {e}")
                conn.close()
                raise
            
            # Create indexes for faster queries - ONLY AFTER verifying columns exist
            try:
                print("Creating database indexes...")
                
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_user_date 
                    ON usage_metrics(user_id, date)
                """)
                
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_tool_source 
                    ON usage_metrics(tool_source)
                """)
                
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_date 
                    ON usage_metrics(date)
                """)
                
                conn.commit()
                print("Database indexes created successfully")
            except Exception as e:
                print(f"Error creating indexes: {e}")
                conn.close()
                raise
            
            conn.close()
            print("Database initialized successfully")
            
        except Exception as e:
            print(f"FATAL ERROR during database initialization: {e}")
            raise
    
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
    
    def get_date_range(self):
        """Get the actual date range coverage from uploaded data.
        
        Returns a tuple of (min_date, max_date) as date objects.
        For monthly data, this returns the full coverage including end of month.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            df = pd.read_sql_query("SELECT MIN(date) as min_date, MAX(date) as max_date FROM usage_metrics", conn)
            conn.close()
            
            if df.empty or pd.isna(df['min_date'].iloc[0]):
                return None, None
            
            min_date = pd.to_datetime(df['min_date'].iloc[0]).date()
            max_date = pd.to_datetime(df['max_date'].iloc[0]).date()
            
            # For monthly data, extend max_date to end of month
            # This allows users to select any date within the month
            max_date = pd.Period(max_date, 'M').end_time.date()
            
            return min_date, max_date
        except Exception as e:
            print(f"Error getting date range: {e}")
            return None, None
    
    def get_unique_users(self):
        """Get unique users."""
        try:
            conn = sqlite3.connect(self.db_path)
            df = pd.read_sql_query("SELECT DISTINCT user_name FROM usage_metrics WHERE user_name IS NOT NULL ORDER BY user_name", conn)
            conn.close()
            return df['user_name'].tolist() if not df.empty else []
        except Exception as e:
            print(f"Error getting users: {e}")
            return []
    
    def get_unique_departments(self):
        """Get unique departments."""
        try:
            conn = sqlite3.connect(self.db_path)
            df = pd.read_sql_query("SELECT DISTINCT department FROM usage_metrics WHERE department IS NOT NULL ORDER BY department", conn)
            conn.close()
            return df['department'].tolist() if not df.empty else []
        except Exception as e:
            print(f"Error getting departments: {e}")
            return []
    
    def get_unique_tools(self):
        """Get unique AI tools in the database."""
        try:
            conn = sqlite3.connect(self.db_path)
            df = pd.read_sql_query("SELECT DISTINCT tool_source FROM usage_metrics WHERE tool_source IS NOT NULL ORDER BY tool_source", conn)
            conn.close()
            return df['tool_source'].tolist() if not df.empty else []
        except Exception as e:
            print(f"Error getting tools: {e}")
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
    
    def get_filtered_data(self, start_date=None, end_date=None, users=None, departments=None, tools=None):
        """Get filtered data with support for multiple filter criteria."""
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Build query dynamically based on filters
            query = "SELECT * FROM usage_metrics WHERE 1=1"
            params = []
            
            if start_date and end_date:
                query += " AND date BETWEEN ? AND ?"
                params.extend([str(start_date), str(end_date)])
            
            if users:
                placeholders = ','.join(['?' for _ in users])
                query += f" AND user_name IN ({placeholders})"
                params.extend(users)
            
            if departments:
                placeholders = ','.join(['?' for _ in departments])
                query += f" AND department IN ({placeholders})"
                params.extend(departments)
            
            if tools:
                placeholders = ','.join(['?' for _ in tools])
                query += f" AND tool_source IN ({placeholders})"
                params.extend(tools)
            
            query += " ORDER BY date DESC"
            
            df = pd.read_sql_query(query, conn, params=params)
            conn.close()
            return df
        except Exception as e:
            print(f"Error getting filtered data: {e}")
            return pd.DataFrame()
    
    def get_tool_comparison_data(self):
        """Get aggregated data for tool comparison."""
        try:
            conn = sqlite3.connect(self.db_path)
            query = """
                SELECT 
                    tool_source,
                    COUNT(DISTINCT user_id) as unique_users,
                    SUM(usage_count) as total_usage,
                    SUM(cost_usd) as total_cost,
                    AVG(usage_count) as avg_usage_per_record
                FROM usage_metrics
                GROUP BY tool_source
                ORDER BY total_usage DESC
            """
            df = pd.read_sql_query(query, conn)
            conn.close()
            return df
        except Exception as e:
            print(f"Error getting tool comparison data: {e}")
            return pd.DataFrame()
    
    def get_user_tool_overlap(self):
        """Get users who use multiple tools."""
        try:
            conn = sqlite3.connect(self.db_path)
            query = """
                SELECT 
                    user_id,
                    user_name,
                    email,
                    COUNT(DISTINCT tool_source) as tool_count,
                    GROUP_CONCAT(DISTINCT tool_source) as tools_used
                FROM usage_metrics
                GROUP BY user_id, user_name, email
                HAVING COUNT(DISTINCT tool_source) > 1
                ORDER BY tool_count DESC
            """
            df = pd.read_sql_query(query, conn)
            conn.close()
            return df
        except Exception as e:
            print(f"Error getting user tool overlap: {e}")
            return pd.DataFrame()
    
    def delete_all_data(self):
        """Delete all data from database."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute("DELETE FROM usage_metrics")
            conn.commit()
            conn.close()
            print("All data deleted successfully")
            return True
        except Exception as e:
            print(f"Error deleting data: {e}")
            return False
    
    def delete_by_file(self, file_source):
        """Delete data from a specific file."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check how many records will be deleted
            cursor.execute("SELECT COUNT(*) FROM usage_metrics WHERE file_source = ?", (file_source,))
            count = cursor.fetchone()[0]
            
            if count > 0:
                conn.execute("DELETE FROM usage_metrics WHERE file_source = ?", (file_source,))
                conn.commit()
                print(f"Deleted {count} records from {file_source}")
            else:
                print(f"No records found for {file_source}")
            
            conn.close()
            return True
        except Exception as e:
            print(f"Error deleting file data: {e}")
            return False
    
    def delete_by_tool(self, tool_source):
        """Delete all data from a specific tool."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check how many records will be deleted
            cursor.execute("SELECT COUNT(*) FROM usage_metrics WHERE tool_source = ?", (tool_source,))
            count = cursor.fetchone()[0]
            
            if count > 0:
                conn.execute("DELETE FROM usage_metrics WHERE tool_source = ?", (tool_source,))
                conn.commit()
                print(f"Deleted {count} records from {tool_source}")
            else:
                print(f"No records found for {tool_source}")
            
            conn.close()
            return True
        except Exception as e:
            print(f"Error deleting tool data: {e}")
            return False
    
    def get_database_stats(self):
        """Get comprehensive database statistics."""
        try:
            conn = sqlite3.connect(self.db_path)
            
            stats = {
                'total_records': 0,
                'unique_users': 0,
                'unique_departments': 0,
                'unique_tools': 0,
                'total_cost': 0.0,
                'date_range': None,
                'records_by_tool': {},
                'records_by_file': {}
            }
            
            # Total records
            cursor = conn.execute("SELECT COUNT(*) FROM usage_metrics")
            stats['total_records'] = cursor.fetchone()[0]
            
            # Unique users
            cursor = conn.execute("SELECT COUNT(DISTINCT user_id) FROM usage_metrics")
            stats['unique_users'] = cursor.fetchone()[0]
            
            # Unique departments
            cursor = conn.execute("SELECT COUNT(DISTINCT department) FROM usage_metrics")
            stats['unique_departments'] = cursor.fetchone()[0]
            
            # Unique tools
            cursor = conn.execute("SELECT COUNT(DISTINCT tool_source) FROM usage_metrics")
            stats['unique_tools'] = cursor.fetchone()[0]
            
            # Total cost
            cursor = conn.execute("SELECT SUM(cost_usd) FROM usage_metrics")
            total_cost = cursor.fetchone()[0]
            stats['total_cost'] = float(total_cost) if total_cost else 0.0
            
            # Date range
            cursor = conn.execute("SELECT MIN(date), MAX(date) FROM usage_metrics")
            min_date, max_date = cursor.fetchone()
            if min_date and max_date:
                stats['date_range'] = f"{min_date} to {max_date}"
            
            # Records by tool
            cursor = conn.execute("SELECT tool_source, COUNT(*) FROM usage_metrics GROUP BY tool_source")
            stats['records_by_tool'] = {row[0]: row[1] for row in cursor.fetchall()}
            
            # Records by file
            cursor = conn.execute("SELECT file_source, COUNT(*) FROM usage_metrics GROUP BY file_source")
            stats['records_by_file'] = {row[0]: row[1] for row in cursor.fetchall()}
            
            conn.close()
            return stats
            
        except Exception as e:
            print(f"Error getting database stats: {e}")
            return None