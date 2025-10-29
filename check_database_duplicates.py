"""
Database Duplicate Detection and Reporting Utility

This script analyzes the existing database to detect potential duplicate records
that may have been added before the duplicate prevention feature was implemented.

Usage:
    python check_database_duplicates.py
    
Output:
    - Summary of files processed
    - Detection of potential duplicate records
    - Recommendations for data cleanup
"""

import os
import sys
import sqlite3
import pandas as pd
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import DatabaseManager


def analyze_database_duplicates(db_path="openai_metrics.db"):
    """
    Analyze database for potential duplicate records.
    
    Args:
        db_path: Path to the database file
        
    Returns:
        dict with analysis results
    """
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        print(f"💡 This is expected if you haven't uploaded any data yet.")
        return None
    
    print("=" * 80)
    print("DATABASE DUPLICATE ANALYSIS")
    print("=" * 80)
    print(f"Database: {db_path}")
    print(f"Analysis time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        db = DatabaseManager(db_path=db_path)
        conn = sqlite3.connect(db_path)
        
        # Get overall statistics
        print("📊 OVERALL STATISTICS")
        print("-" * 80)
        
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM usage_metrics")
        total_records = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT user_id) FROM usage_metrics")
        unique_users = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT file_source) FROM usage_metrics WHERE file_source IS NOT NULL")
        unique_files = cursor.fetchone()[0]
        
        print(f"Total Records: {total_records:,}")
        print(f"Unique Users: {unique_users:,}")
        print(f"Files Processed: {unique_files:,}")
        print()
        
        # Get file summary
        print("📁 FILES PROCESSED")
        print("-" * 80)
        
        files_summary = db.get_processed_files_summary()
        if not files_summary.empty:
            # Format the summary nicely
            for idx, row in files_summary.iterrows():
                print(f"\n{idx + 1}. {row['file_source']}")
                print(f"   Tool: {row['tool_source']}")
                print(f"   Records: {row['record_count']:,}")
                print(f"   Users: {row['user_count']:,}")
                print(f"   Date Range: {row['min_date']} to {row['max_date']}")
                if pd.notna(row['created_at']):
                    print(f"   Uploaded: {row['created_at']}")
        else:
            print("No files found in database")
        
        print("\n")
        
        # Check for potential duplicates
        print("🔍 DUPLICATE DETECTION")
        print("-" * 80)
        
        # Method 1: Check for exact duplicate rows (same user, date, feature, tool)
        duplicate_query = """
            SELECT 
                user_id, 
                date, 
                feature_used, 
                tool_source,
                COUNT(*) as occurrence_count,
                GROUP_CONCAT(DISTINCT file_source) as source_files
            FROM usage_metrics
            GROUP BY user_id, date, feature_used, tool_source
            HAVING occurrence_count > 1
            ORDER BY occurrence_count DESC
            LIMIT 20
        """
        
        duplicates_df = pd.read_sql_query(duplicate_query, conn)
        
        if not duplicates_df.empty:
            print(f"⚠️  Found {len(duplicates_df)} potential duplicate record patterns")
            print(f"    (showing top 20)")
            print()
            
            total_duplicate_records = duplicates_df['occurrence_count'].sum() - len(duplicates_df)
            print(f"📈 Estimated duplicate records: {total_duplicate_records:,}")
            print()
            
            print("Top duplicates:")
            for idx, row in duplicates_df.head(10).iterrows():
                print(f"\n  {idx + 1}. User: {row['user_id']}")
                print(f"     Date: {row['date']}, Feature: {row['feature_used']}")
                print(f"     Occurrences: {row['occurrence_count']}")
                print(f"     Source files: {row['source_files']}")
        else:
            print("✅ No duplicate records detected!")
            print("   Your database is clean - each user/date/feature combination appears only once.")
        
        print("\n")
        
        # Method 2: Check for files that might have been uploaded multiple times
        file_pattern_query = """
            SELECT 
                file_source,
                COUNT(*) as times_processed
            FROM (
                SELECT DISTINCT file_source, created_at
                FROM usage_metrics
                WHERE file_source IS NOT NULL
            )
            GROUP BY file_source
            HAVING times_processed > 1
        """
        
        file_duplicates_df = pd.read_sql_query(file_pattern_query, conn)
        
        if not file_duplicates_df.empty:
            print("⚠️  FILES POTENTIALLY PROCESSED MULTIPLE TIMES")
            print("-" * 80)
            for idx, row in file_duplicates_df.iterrows():
                print(f"{idx + 1}. {row['file_source']}: processed {row['times_processed']} times")
            print()
        
        # Recommendations
        print("💡 RECOMMENDATIONS")
        print("-" * 80)
        
        if not duplicates_df.empty:
            print("\n⚠️  Duplicates detected in your database:")
            print("   1. Review the duplicate list above to confirm they are true duplicates")
            print("   2. Identify which file(s) contain the duplicate data")
            print("   3. Go to Database Management tab in the app")
            print("   4. Delete the duplicate file(s) using the 🗑️ button")
            print("   5. Re-upload the file if needed (it will be protected by duplicate prevention)")
            print()
            print("   Alternative: Clear all data and re-upload your 45 files")
            print("              (the new duplicate prevention will protect against re-processing)")
        else:
            print("\n✅ Your database looks clean!")
            print("   - No duplicate records detected")
            print("   - Duplicate prevention is now active for all future uploads")
            print("   - You can safely upload your remaining files")
        
        conn.close()
        
        print("\n" + "=" * 80)
        
        return {
            'total_records': total_records,
            'unique_users': unique_users,
            'unique_files': unique_files,
            'duplicates_found': len(duplicates_df) > 0,
            'duplicate_patterns': len(duplicates_df)
        }
        
    except Exception as e:
        print(f"❌ Error analyzing database: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    # Check for custom database path argument
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
    else:
        db_path = "openai_metrics.db"
    
    print(f"\n🔎 Analyzing database: {db_path}\n")
    results = analyze_database_duplicates(db_path)
    
    if results:
        print(f"\n✅ Analysis complete!")
        if results['duplicates_found']:
            print(f"⚠️  Action needed: Review and clean up {results['duplicate_patterns']} duplicate patterns")
            sys.exit(1)
        else:
            print(f"✅ Database is clean and ready for use")
            sys.exit(0)
    else:
        print(f"\n❌ Analysis could not be completed")
        sys.exit(1)
