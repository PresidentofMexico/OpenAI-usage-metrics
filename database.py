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
                    last_day_active TEXT,
                    first_day_active_in_period TEXT,
                    last_day_active_in_period TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create employees table for master employee list
            conn.execute("""
                CREATE TABLE IF NOT EXISTS employees (
                    employee_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    first_name TEXT,
                    last_name TEXT,
                    email TEXT UNIQUE,
                    title TEXT,
                    department TEXT,
                    status TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
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
            
            # Migrate activity date columns if needed
            cursor = conn.execute("PRAGMA table_info(usage_metrics)")
            columns = [row[1] for row in cursor.fetchall()]
            
            if 'last_day_active' not in columns:
                try:
                    print("Migrating database: Adding 'last_day_active' column...")
                    conn.execute("ALTER TABLE usage_metrics ADD COLUMN last_day_active TEXT")
                    conn.commit()
                except Exception as e:
                    print(f"Error adding last_day_active column: {e}")
                    conn.close()
                    raise
            
            if 'first_day_active_in_period' not in columns:
                try:
                    print("Migrating database: Adding 'first_day_active_in_period' column...")
                    conn.execute("ALTER TABLE usage_metrics ADD COLUMN first_day_active_in_period TEXT")
                    conn.commit()
                except Exception as e:
                    print(f"Error adding first_day_active_in_period column: {e}")
                    conn.close()
                    raise
            
            if 'last_day_active_in_period' not in columns:
                try:
                    print("Migrating database: Adding 'last_day_active_in_period' column...")
                    conn.execute("ALTER TABLE usage_metrics ADD COLUMN last_day_active_in_period TEXT")
                    conn.commit()
                except Exception as e:
                    print(f"Error adding last_day_active_in_period column: {e}")
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
                
                # Create indexes for employees table
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_employee_email 
                    ON employees(email)
                """)
                
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_employee_department 
                    ON employees(department)
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
                # Use errors='coerce' to handle invalid dates gracefully
                dates = pd.to_datetime(df['date'], errors='coerce').dropna().dt.date.tolist()
                return dates
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
            
            # Use errors='coerce' to handle invalid dates gracefully
            min_date = pd.to_datetime(df['min_date'].iloc[0], errors='coerce')
            max_date = pd.to_datetime(df['max_date'].iloc[0], errors='coerce')
            
            # Check if dates are valid
            if pd.isna(min_date) or pd.isna(max_date):
                print(f"Warning: Invalid dates in database - min: {df['min_date'].iloc[0]}, max: {df['max_date'].iloc[0]}")
                return None, None
            
            min_date = min_date.date()
            max_date = max_date.date()
            
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
    
    def get_superseding_preview(self, tool_source, months, users):
        """
        Get preview of records that will be superseded (deleted) for given months and users.
        
        Args:
            tool_source: Tool source name (e.g., 'ChatGPT', 'BlueFlame AI')
            months: List of month period strings (e.g., ['2025-01', '2025-02'])
            users: List of user IDs
            
        Returns:
            dict: Summary of records that will be affected
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Build query to count affected records
            month_conditions = []
            params = [tool_source]
            
            for month_str in months:
                # Parse month string to period
                try:
                    month_period = pd.Period(month_str, 'M')
                    month_start = month_period.to_timestamp().strftime('%Y-%m-%d')
                    month_end = (month_period + 1).to_timestamp().strftime('%Y-%m-%d')
                    month_conditions.append(f"(date >= ? AND date < ?)")
                    params.extend([month_start, month_end])
                except:
                    continue
            
            if not month_conditions:
                conn.close()
                return {'total_records': 0, 'affected_users': 0, 'months': []}
            
            # Build user condition
            user_placeholders = ','.join(['?' for _ in users])
            params.extend(users)
            
            query = f"""
                SELECT 
                    COUNT(*) as total_records,
                    COUNT(DISTINCT user_id) as affected_users,
                    COUNT(DISTINCT date) as affected_dates
                FROM usage_metrics
                WHERE tool_source = ?
                AND ({' OR '.join(month_conditions)})
                AND user_id IN ({user_placeholders})
            """
            
            cursor.execute(query, params)
            result = cursor.fetchone()
            
            conn.close()
            
            return {
                'total_records': result[0] if result else 0,
                'affected_users': result[1] if result else 0,
                'affected_dates': result[2] if result else 0,
                'months': months
            }
            
        except Exception as e:
            print(f"Error getting superseding preview: {e}")
            return {'total_records': 0, 'affected_users': 0, 'months': []}
    
    def detect_duplicates(self):
        """
        Detect duplicate records based on (user_id, date, feature_used, tool_source).
        
        Returns:
            DataFrame with duplicate record information
        """
        try:
            conn = sqlite3.connect(self.db_path)
            query = """
                SELECT 
                    user_id,
                    date,
                    feature_used,
                    tool_source,
                    COUNT(*) as duplicate_count,
                    SUM(usage_count) as total_usage,
                    GROUP_CONCAT(id) as record_ids
                FROM usage_metrics
                GROUP BY user_id, date, feature_used, tool_source
                HAVING COUNT(*) > 1
                ORDER BY duplicate_count DESC, total_usage DESC
            """
            df = pd.read_sql_query(query, conn)
            conn.close()
            return df
        except Exception as e:
            print(f"Error detecting duplicates: {e}")
            return pd.DataFrame()
    
    def load_employees(self, df):
        """
        Load or update employee records from a DataFrame.
        Supports files with or without email column - uses name-based matching as fallback.
        
        Args:
            df: DataFrame with employee data
            
        Returns:
            tuple: (success: bool, message: str, count: int)
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            inserted = 0
            updated = 0
            
            for _, row in df.iterrows():
                # Handle potential NaN/float values by converting to string and stripping
                # Defensive None checking: ensure value is not None before calling str() and strip()
                def safe_str_strip(value):
                    """Safely convert value to string and strip, handling None/NaN/empty"""
                    if value is None or pd.isna(value):
                        return ''
                    if isinstance(value, str):
                        stripped = value.strip()
                        # Return empty string if it's just whitespace or common null representations
                        if not stripped or stripped.lower() in ('none', 'nan', 'null', 'n/a'):
                            return ''
                        return stripped
                    # For non-string types, convert to string
                    str_val = str(value).strip()
                    if str_val.lower() in ('none', 'nan', 'null', 'n/a'):
                        return ''
                    return str_val
                
                first_name = safe_str_strip(row.get('first_name', ''))
                last_name = safe_str_strip(row.get('last_name', ''))
                
                # Email requires special handling - should be None if not valid
                email_raw = row.get('email')
                if email_raw is None or pd.isna(email_raw):
                    email = None
                elif isinstance(email_raw, str):
                    email_stripped = email_raw.strip().lower()
                    # Check for empty, whitespace-only, or common null string representations
                    if not email_stripped or email_stripped in ('none', 'nan', 'null', 'n/a'):
                        email = None
                    else:
                        email = email_stripped
                else:
                    # Handle non-string types (e.g., float nan)
                    email_str = str(email_raw).strip().lower()
                    if not email_str or email_str in ('none', 'nan', 'null', 'n/a'):
                        email = None
                    else:
                        email = email_str
                
                title = safe_str_strip(row.get('title', ''))
                department = safe_str_strip(row.get('department', ''))
                status = safe_str_strip(row.get('status', ''))
                
                # Skip if we don't have valid first and last names
                if not first_name or not last_name:
                    continue
                
                # Check if employee exists - first by email if available, then by name
                existing = None
                if email:
                    cursor.execute("SELECT employee_id FROM employees WHERE LOWER(email) = ?", (email,))
                    existing = cursor.fetchone()
                
                if not existing:
                    # Try to find by name
                    cursor.execute(
                        "SELECT employee_id FROM employees WHERE LOWER(first_name) = ? AND LOWER(last_name) = ?",
                        (first_name.lower(), last_name.lower())
                    )
                    existing = cursor.fetchone()
                
                if existing:
                    # Update existing employee
                    cursor.execute("""
                        UPDATE employees 
                        SET first_name = ?, last_name = ?, email = ?, title = ?, department = ?, status = ?, updated_at = ?
                        WHERE employee_id = ?
                    """, (
                        first_name,
                        last_name,
                        email,
                        title,
                        department,
                        status,
                        datetime.now().isoformat(),
                        existing[0]
                    ))
                    updated += 1
                else:
                    # Insert new employee
                    cursor.execute("""
                        INSERT INTO employees (first_name, last_name, email, title, department, status, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        first_name,
                        last_name,
                        email,
                        title,
                        department,
                        status,
                        datetime.now().isoformat(),
                        datetime.now().isoformat()
                    ))
                    inserted += 1
            
            conn.commit()
            conn.close()
            
            total = inserted + updated
            message = f"Loaded {total} employees ({inserted} new, {updated} updated)"
            print(message)
            return True, message, total
            
        except Exception as e:
            print(f"Error loading employees: {e}")
            import traceback
            traceback.print_exc()
            return False, f"Error loading employees: {str(e)}", 0
    
    def get_employee_by_email(self, email):
        """
        Get employee record by email.
        
        Args:
            email: Employee email address
            
        Returns:
            dict or None: Employee record
        """
        try:
            # Check if email is None or empty before calling strip()
            if not email:
                return None
            
            # Strip and check if empty
            email_stripped = email.strip() if isinstance(email, str) else str(email).strip()
            if not email_stripped:
                return None
                
            conn = sqlite3.connect(self.db_path)
            cursor = conn.execute(
                "SELECT employee_id, first_name, last_name, email, title, department, status FROM employees WHERE LOWER(email) = ?",
                (email_stripped.lower(),)
            )
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return {
                    'employee_id': row[0],
                    'first_name': row[1],
                    'last_name': row[2],
                    'email': row[3],
                    'title': row[4],
                    'department': row[5],
                    'status': row[6]
                }
            return None
            
        except Exception as e:
            print(f"Error getting employee: {e}")
            return None
    
    def get_employee_by_name(self, first_name, last_name):
        """
        Get employee record by first and last name.
        
        Args:
            first_name: Employee first name
            last_name: Employee last name
            
        Returns:
            dict or None: Employee record
        """
        try:
            # Check if either name is None or empty
            if not first_name or not last_name:
                return None
            
            # Strip and check - handle both string and other types
            first_name_stripped = first_name.strip() if isinstance(first_name, str) else str(first_name).strip()
            last_name_stripped = last_name.strip() if isinstance(last_name, str) else str(last_name).strip()
            
            if not first_name_stripped or not last_name_stripped:
                return None
                
            conn = sqlite3.connect(self.db_path)
            cursor = conn.execute(
                "SELECT employee_id, first_name, last_name, email, title, department, status FROM employees WHERE LOWER(first_name) = ? AND LOWER(last_name) = ?",
                (first_name_stripped.lower(), last_name_stripped.lower())
            )
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return {
                    'employee_id': row[0],
                    'first_name': row[1],
                    'last_name': row[2],
                    'email': row[3],
                    'title': row[4],
                    'department': row[5],
                    'status': row[6]
                }
            return None
            
        except Exception as e:
            print(f"Error getting employee by name: {e}")
            return None
    
    def get_all_employees(self):
        """Get all employee records."""
        try:
            conn = sqlite3.connect(self.db_path)
            df = pd.read_sql_query(
                "SELECT employee_id, first_name, last_name, email, title, department, status FROM employees ORDER BY last_name, first_name",
                conn
            )
            conn.close()
            return df
        except Exception as e:
            print(f"Error getting employees: {e}")
            return pd.DataFrame()
    
    def get_employee_departments(self):
        """Get unique departments from employee table."""
        try:
            conn = sqlite3.connect(self.db_path)
            df = pd.read_sql_query(
                "SELECT DISTINCT department FROM employees WHERE department IS NOT NULL AND department != '' ORDER BY department",
                conn
            )
            conn.close()
            return df['department'].tolist() if not df.empty else []
        except Exception as e:
            print(f"Error getting employee departments: {e}")
            return []
    
    def get_unidentified_users(self):
        """
        Get users from usage_metrics who are not in the employees table.
        Checks both email and name-based matching.
        
        Returns:
            DataFrame with unidentified users and their usage stats
        """
        try:
            conn = sqlite3.connect(self.db_path)
            query = """
                SELECT 
                    um.email,
                    CASE 
                        WHEN um.user_name IS NULL OR TRIM(um.user_name) = '' THEN 'Unknown User'
                        ELSE um.user_name
                    END as user_name,
                    COALESCE(GROUP_CONCAT(DISTINCT um.tool_source), 'Unknown') as tools_used,
                    COALESCE(SUM(um.usage_count), 0) as total_usage,
                    COALESCE(SUM(um.cost_usd), 0.0) as total_cost,
                    COUNT(DISTINCT um.date) as days_active
                FROM usage_metrics um
                LEFT JOIN employees e ON (
                    LOWER(um.email) = LOWER(e.email) 
                    OR (
                        um.user_name IS NOT NULL 
                        AND um.user_name != ''
                        AND LOWER(SUBSTR(um.user_name, 1, INSTR(um.user_name || ' ', ' ') - 1)) = LOWER(e.first_name)
                        AND LOWER(SUBSTR(um.user_name, INSTR(um.user_name, ' ') + 1)) = LOWER(e.last_name)
                    )
                )
                WHERE e.employee_id IS NULL AND um.email IS NOT NULL AND um.email != ''
                GROUP BY um.email, um.user_name
                ORDER BY total_usage DESC
            """
            df = pd.read_sql_query(query, conn)
            conn.close()
            return df
        except Exception as e:
            print(f"Error getting unidentified users: {e}")
            return pd.DataFrame()
    
    def get_employee_count(self):
        """Get count of employees in the database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.execute("SELECT COUNT(*) FROM employees")
            count = cursor.fetchone()[0]
            conn.close()
            return count
        except Exception as e:
            print(f"Error getting employee count: {e}")
            return 0
    
    def delete_employee(self, employee_id):
        """
        Delete an employee from the employees table.
        
        Args:
            employee_id: The employee_id to delete
            
        Returns:
            tuple: (success: bool, message: str)
        """
        try:
            # Convert numpy int64 to regular int
            if hasattr(employee_id, 'item'):
                employee_id = int(employee_id.item())
            else:
                employee_id = int(employee_id)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # First check if employee exists
            cursor.execute("SELECT first_name, last_name, email FROM employees WHERE employee_id = ?", (employee_id,))
            employee = cursor.fetchone()
            
            if not employee:
                conn.close()
                return False, "Employee not found"
            
            first_name, last_name, email = employee
            
            # Delete the employee
            cursor.execute("DELETE FROM employees WHERE employee_id = ?", (employee_id,))
            conn.commit()
            conn.close()
            
            message = f"Successfully deleted employee: {first_name} {last_name}"
            if email:
                message += f" ({email})"
            
            print(message)
            return True, message
            
        except Exception as e:
            print(f"Error deleting employee: {e}")
            return False, f"Error deleting employee: {str(e)}"
            return False, f"Error deleting employee: {str(e)}"
    
    def delete_employee_usage(self, email):
        """
        Delete all usage metrics for a specific employee email.
        This removes the employee's data from analytics while keeping the employee record.
        
        Args:
            email: The employee email to delete usage for
            
        Returns:
            tuple: (success: bool, message: str, records_deleted: int)
        """
        try:
            if not email:
                return False, "No email provided", 0
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Count records to be deleted
            cursor.execute("SELECT COUNT(*) FROM usage_metrics WHERE LOWER(email) = ?", (email.lower(),))
            count = cursor.fetchone()[0]
            
            if count == 0:
                conn.close()
                return True, "No usage data found for this email", 0
            
            # Delete usage records
            cursor.execute("DELETE FROM usage_metrics WHERE LOWER(email) = ?", (email.lower(),))
            conn.commit()
            conn.close()
            
            message = f"Deleted {count} usage record(s) for {email}"
            print(message)
            return True, message, count
            
        except Exception as e:
            print(f"Error deleting employee usage: {e}")
            return False, f"Error deleting usage data: {str(e)}", 0
    
    def delete_employee_and_usage(self, employee_id):
        """
        Delete an employee and all their usage metrics.
        This is a complete removal from the system.
        
        Args:
            employee_id: The employee_id to delete
            
        Returns:
            tuple: (success: bool, message: str)
        """
        try:
            # Convert numpy int64 to regular int
            if hasattr(employee_id, 'item'):
                employee_id = int(employee_id.item())
            else:
                employee_id = int(employee_id)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get employee info first
            cursor.execute("SELECT first_name, last_name, email FROM employees WHERE employee_id = ?", (employee_id,))
            employee = cursor.fetchone()
            
            if not employee:
                conn.close()
                return False, "Employee not found"
            
            first_name, last_name, email = employee
            conn.close()
            
            # Delete usage data if email exists
            usage_deleted = 0
            if email:
                success, message, usage_deleted = self.delete_employee_usage(email)
                if not success:
                    return False, f"Error deleting usage data: {message}"
            
            # Delete employee record
            success, message = self.delete_employee(employee_id)
            if not success:
                return False, message
            
            final_message = f"Successfully deleted employee {first_name} {last_name}"
            if email:
                final_message += f" ({email})"
            if usage_deleted > 0:
                final_message += f" and {usage_deleted} usage record(s)"
            
            return True, final_message
            
        except Exception as e:
            print(f"Error in delete_employee_and_usage: {e}")
            return False, f"Error: {str(e)}"