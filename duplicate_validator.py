"""
Duplicate Data Validator

Validates that user message counts are not duplicated due to overlapping weekly and monthly data files.
This utility ensures data integrity by detecting and reporting duplicate message counts in the database.

Features:
- Detects duplicate records by user/period/feature combinations
- Validates that total message counts match unique message totals (no double-counting)
- Generates detailed per-user validation reports
- Identifies specific duplicate sources (file overlaps)
- Provides summary statistics and actionable insights

Usage:
    from duplicate_validator import DuplicateValidator
    
    validator = DuplicateValidator(db_manager)
    results = validator.validate_duplicates()
    report = validator.generate_report(results)
    print(report)
"""

import pandas as pd
import sqlite3
from datetime import datetime
from typing import Dict, Any, List, Tuple
from database import DatabaseManager


class DuplicateValidator:
    """Validates that usage data is not duplicated due to overlapping file imports."""
    
    def __init__(self, db_manager: DatabaseManager):
        """
        Initialize the duplicate validator.
        
        Args:
            db_manager: DatabaseManager instance for database access
        """
        self.db = db_manager
        self.message_features = ['ChatGPT Messages', 'GPT Messages', 'Tool Messages', 'Project Messages']
    
    def validate_duplicates(self) -> Dict[str, Any]:
        """
        Validate that user message counts are not duplicated.
        
        Returns:
            Dictionary with comprehensive validation results
        """
        validation_results = {
            'timestamp': datetime.now().isoformat(),
            'overall_status': 'PASS',
            'total_users_checked': 0,
            'users_with_duplicates': 0,
            'duplicate_records_found': 0,
            'users': [],
            'summary': {}
        }
        
        try:
            # Get all usage data
            conn = sqlite3.connect(self.db.db_path)
            
            # Query to find duplicate records (same user, date, feature, tool)
            duplicate_query = """
                SELECT 
                    email,
                    user_name,
                    date,
                    feature_used,
                    tool_source,
                    COUNT(*) as record_count,
                    SUM(usage_count) as total_usage,
                    GROUP_CONCAT(file_source) as files,
                    GROUP_CONCAT(id) as record_ids
                FROM usage_metrics
                WHERE email IS NOT NULL
                GROUP BY email, date, feature_used, tool_source
                HAVING COUNT(*) > 1
                ORDER BY email, date, feature_used
            """
            
            duplicates_df = pd.read_sql_query(duplicate_query, conn)
            
            # Query to get per-user totals across all records (including duplicates)
            user_totals_query = """
                SELECT 
                    email,
                    user_name,
                    department,
                    feature_used,
                    COUNT(*) as total_records,
                    SUM(usage_count) as total_messages,
                    COUNT(DISTINCT date) as unique_periods,
                    COUNT(DISTINCT file_source) as file_count,
                    GROUP_CONCAT(DISTINCT file_source) as files
                FROM usage_metrics
                WHERE email IS NOT NULL AND feature_used IN ('ChatGPT Messages', 'GPT Messages', 'Tool Messages', 'Project Messages')
                GROUP BY email, user_name, department, feature_used
                ORDER BY email, feature_used
            """
            
            user_totals_df = pd.read_sql_query(user_totals_query, conn)
            
            # Query to get unique message counts (deduplicated by user/date/feature)
            unique_totals_query = """
                SELECT 
                    email,
                    feature_used,
                    COUNT(DISTINCT date) as unique_periods,
                    SUM(CASE 
                        WHEN record_count = 1 THEN usage_count
                        ELSE CAST(usage_count AS REAL) / record_count
                    END) as dedup_messages
                FROM (
                    SELECT 
                        email,
                        date,
                        feature_used,
                        usage_count,
                        COUNT(*) OVER (PARTITION BY email, date, feature_used, tool_source) as record_count
                    FROM usage_metrics
                    WHERE email IS NOT NULL AND feature_used IN ('ChatGPT Messages', 'GPT Messages', 'Tool Messages', 'Project Messages')
                )
                GROUP BY email, feature_used
            """
            
            unique_totals_df = pd.read_sql_query(unique_totals_query, conn)
            conn.close()
            
            # Process duplicates
            validation_results['duplicate_records_found'] = len(duplicates_df)
            
            if not duplicates_df.empty:
                validation_results['overall_status'] = 'DUPLICATES_FOUND'
                validation_results['duplicate_details'] = duplicates_df.to_dict('records')
            
            # Process user-level validation
            if not user_totals_df.empty:
                # Merge with unique totals to compare
                user_validation = user_totals_df.merge(
                    unique_totals_df[['email', 'feature_used', 'dedup_messages']],
                    on=['email', 'feature_used'],
                    how='left'
                )
                
                # Calculate duplication factor
                user_validation['dedup_messages'] = user_validation['dedup_messages'].fillna(user_validation['total_messages'])
                user_validation['duplication_factor'] = (
                    user_validation['total_messages'] / user_validation['dedup_messages']
                ).round(2)
                user_validation['is_duplicated'] = user_validation['duplication_factor'] > 1.01
                
                # Get unique users
                unique_users = user_validation['email'].unique()
                validation_results['total_users_checked'] = len(unique_users)
                
                # Identify users with duplicates
                duplicated_users = user_validation[user_validation['is_duplicated']]['email'].unique()
                validation_results['users_with_duplicates'] = len(duplicated_users)
                
                # Build per-user summaries
                for user_email in unique_users:
                    user_data = user_validation[user_validation['email'] == user_email]
                    
                    # Get user name and department from first record
                    user_name = user_data['user_name'].iloc[0]
                    department = user_data['department'].iloc[0] if 'department' in user_data.columns else 'Unknown'
                    
                    # Calculate totals across all features
                    total_messages = user_data['total_messages'].sum()
                    total_dedup_messages = user_data['dedup_messages'].sum()
                    has_duplicates = user_data['is_duplicated'].any()
                    
                    # Get feature breakdown
                    features = []
                    for _, row in user_data.iterrows():
                        features.append({
                            'feature': row['feature_used'],
                            'total_messages': int(row['total_messages']),
                            'unique_messages': int(row['dedup_messages']),
                            'records': int(row['total_records']),
                            'periods': int(row['unique_periods']),
                            'files': row['file_count'],
                            'is_duplicated': bool(row['is_duplicated']),
                            'duplication_factor': float(row['duplication_factor'])
                        })
                    
                    user_summary = {
                        'email': user_email,
                        'user_name': user_name,
                        'department': department,
                        'total_messages': int(total_messages),
                        'unique_messages': int(total_dedup_messages),
                        'duplicate_messages': int(total_messages - total_dedup_messages),
                        'has_duplicates': has_duplicates,
                        'validation_status': 'FAIL' if has_duplicates else 'PASS',
                        'features': features
                    }
                    
                    validation_results['users'].append(user_summary)
                
                # Add summary statistics
                validation_results['summary'] = {
                    'total_messages_in_db': int(user_validation['total_messages'].sum()),
                    'unique_messages': int(user_validation['dedup_messages'].sum()),
                    'duplicate_messages': int(user_validation['total_messages'].sum() - user_validation['dedup_messages'].sum()),
                    'duplication_percentage': round(
                        ((user_validation['total_messages'].sum() / user_validation['dedup_messages'].sum() - 1) * 100)
                        if user_validation['dedup_messages'].sum() > 0 else 0,
                        2
                    )
                }
            
        except Exception as e:
            validation_results['overall_status'] = 'ERROR'
            validation_results['error'] = str(e)
            import traceback
            validation_results['error_details'] = traceback.format_exc()
        
        return validation_results
    
    def get_duplicate_details(self, email: str = None) -> pd.DataFrame:
        """
        Get detailed duplicate information for a specific user or all users.
        
        Args:
            email: Optional user email to filter by
            
        Returns:
            DataFrame with duplicate record details
        """
        try:
            conn = sqlite3.connect(self.db.db_path)
            
            query = """
                SELECT 
                    um.id,
                    um.email,
                    um.user_name,
                    um.department,
                    um.date,
                    um.feature_used,
                    um.usage_count,
                    um.tool_source,
                    um.file_source,
                    um.created_at,
                    dup.record_count,
                    dup.total_usage as group_total
                FROM usage_metrics um
                INNER JOIN (
                    SELECT 
                        email,
                        date,
                        feature_used,
                        tool_source,
                        COUNT(*) as record_count,
                        SUM(usage_count) as total_usage
                    FROM usage_metrics
                    WHERE email IS NOT NULL
                    GROUP BY email, date, feature_used, tool_source
                    HAVING COUNT(*) > 1
                ) dup ON um.email = dup.email 
                    AND um.date = dup.date 
                    AND um.feature_used = dup.feature_used 
                    AND um.tool_source = dup.tool_source
            """
            
            if email:
                query += " WHERE um.email = ?"
                df = pd.read_sql_query(query, conn, params=(email,))
            else:
                df = pd.read_sql_query(query, conn)
            
            conn.close()
            return df
            
        except Exception as e:
            print(f"Error getting duplicate details: {e}")
            return pd.DataFrame()
    
    def generate_report(self, results: Dict[str, Any], format: str = 'text') -> str:
        """
        Generate a human-readable validation report.
        
        Args:
            results: Validation results dictionary
            format: 'text' or 'json'
            
        Returns:
            Formatted report string
        """
        if format == 'json':
            import json
            return json.dumps(results, indent=2)
        
        # Text format
        lines = []
        lines.append("=" * 80)
        lines.append("Duplicate Data Validation Report")
        lines.append("=" * 80)
        lines.append(f"Generated: {results.get('timestamp', 'N/A')}")
        lines.append("")
        
        # Overall status
        status = results.get('overall_status', 'UNKNOWN')
        status_symbols = {
            'PASS': '✅',
            'DUPLICATES_FOUND': '⚠️',
            'ERROR': '🚫'
        }
        status_symbol = status_symbols.get(status, '❓')
        
        lines.append(f"Overall Status: {status_symbol} {status}")
        lines.append("")
        
        if 'error' in results:
            lines.append(f"Error: {results['error']}")
            lines.append("=" * 80)
            return '\n'.join(lines)
        
        # Summary statistics
        lines.append("Summary:")
        lines.append("-" * 80)
        lines.append(f"Total Users Checked: {results.get('total_users_checked', 0)}")
        lines.append(f"Users with Duplicates: {results.get('users_with_duplicates', 0)}")
        lines.append(f"Duplicate Records Found: {results.get('duplicate_records_found', 0)}")
        
        if 'summary' in results and results['summary']:
            summary = results['summary']
            lines.append(f"\nMessage Counts:")
            lines.append(f"  Total Messages in DB: {summary.get('total_messages_in_db', 0):,}")
            lines.append(f"  Unique Messages: {summary.get('unique_messages', 0):,}")
            lines.append(f"  Duplicate Messages: {summary.get('duplicate_messages', 0):,}")
            lines.append(f"  Duplication Rate: {summary.get('duplication_percentage', 0)}%")
        
        lines.append("")
        
        # User-level details (show top 20 users with highest message counts)
        if 'users' in results and results['users']:
            # Sort by total messages descending
            sorted_users = sorted(results['users'], key=lambda x: x['total_messages'], reverse=True)
            
            lines.append("Top Users by Message Count:")
            lines.append("-" * 80)
            
            for i, user in enumerate(sorted_users[:20], 1):
                user_symbol = '❌' if user['has_duplicates'] else '✅'
                lines.append(f"\n{i}. {user_symbol} {user['user_name']} ({user['email']})")
                lines.append(f"   Department: {user['department']}")
                lines.append(f"   Total Messages: {user['total_messages']:,}")
                lines.append(f"   Unique Messages: {user['unique_messages']:,}")
                
                if user['has_duplicates']:
                    lines.append(f"   ⚠️  Duplicate Messages: {user['duplicate_messages']:,}")
                    lines.append(f"   Status: {user['validation_status']}")
                    
                    # Show feature breakdown for duplicated users
                    lines.append(f"   Feature Breakdown:")
                    for feature in user['features']:
                        if feature['is_duplicated']:
                            lines.append(f"     - {feature['feature']}: {feature['total_messages']:,} total, "
                                       f"{feature['unique_messages']:,} unique "
                                       f"(x{feature['duplication_factor']} duplication)")
        
        # Duplicate record details
        if 'duplicate_details' in results and results['duplicate_details']:
            lines.append("\n" + "-" * 80)
            lines.append("Duplicate Record Details (Top 10):")
            lines.append("-" * 80)
            
            for i, dup in enumerate(results['duplicate_details'][:10], 1):
                lines.append(f"\n{i}. {dup['user_name']} ({dup['email']})")
                lines.append(f"   Date: {dup['date']}")
                lines.append(f"   Feature: {dup['feature_used']}")
                lines.append(f"   Tool: {dup['tool_source']}")
                lines.append(f"   Duplicate Records: {dup['record_count']}")
                lines.append(f"   Total Usage: {dup['total_usage']}")
                lines.append(f"   Files: {dup['files']}")
        
        lines.append("\n" + "=" * 80)
        
        return '\n'.join(lines)
    
    def get_user_validation_status(self, email: str) -> Dict[str, Any]:
        """
        Get validation status for a specific user.
        
        Args:
            email: User email address
            
        Returns:
            Dictionary with user validation details
        """
        results = self.validate_duplicates()
        
        if 'users' in results:
            for user in results['users']:
                if user['email'].lower() == email.lower():
                    return user
        
        return {
            'email': email,
            'validation_status': 'NOT_FOUND',
            'message': 'User not found in database'
        }


def main():
    """Example usage of DuplicateValidator."""
    
    # Initialize database
    db = DatabaseManager()
    
    # Initialize validator
    validator = DuplicateValidator(db)
    
    # Run validation
    print("Running duplicate validation...")
    print("")
    
    results = validator.validate_duplicates()
    
    # Generate and display report
    print(validator.generate_report(results, format='text'))
    
    # Show duplicate details if any found
    if results.get('duplicate_records_found', 0) > 0:
        print("\n" + "=" * 80)
        print("Detailed Duplicate Records:")
        print("=" * 80)
        duplicate_details = validator.get_duplicate_details()
        if not duplicate_details.empty:
            print(duplicate_details.to_string())


if __name__ == "__main__":
    main()
