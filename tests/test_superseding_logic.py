"""
Test suite for universal data superseding logic.

Tests that CSV re-uploads replace data for covered months/users instead of accumulating.
"""
import unittest
import pandas as pd
import tempfile
import os
import sqlite3
from datetime import datetime, timedelta
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database import DatabaseManager
from data_processor import DataProcessor


class TestSupersedingLogic(unittest.TestCase):
    """Test data superseding for both BlueFlame and OpenAI uploads."""
    
    def setUp(self):
        """Set up test database and processor."""
        # Create temporary database
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        
        self.db = DatabaseManager(self.temp_db.name)
        self.processor = DataProcessor(self.db)
    
    def tearDown(self):
        """Clean up test database."""
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
    
    def test_openai_superseding_single_user_single_month(self):
        """Test that OpenAI re-upload replaces data for same user and month."""
        # First upload - user1 in January 2025
        first_data = pd.DataFrame([
            {
                'user_id': 'user1@company.com',
                'user_name': 'User One',
                'email': 'user1@company.com',
                'department': 'Engineering',
                'date': '2025-01-01',
                'feature_used': 'ChatGPT Messages',
                'usage_count': 100,
                'cost_usd': 60.0,
                'tool_source': 'ChatGPT',
                'file_source': 'upload1.csv'
            }
        ])
        
        # Process first upload
        success, message = self.processor.process_monthly_data(first_data, 'upload1.csv')
        self.assertTrue(success)
        
        # Verify first upload
        all_data = self.db.get_all_data()
        self.assertEqual(len(all_data), 1)
        self.assertEqual(all_data.iloc[0]['usage_count'], 100)
        self.assertEqual(all_data.iloc[0]['file_source'], 'upload1.csv')
        
        # Second upload - same user, same month, different count
        second_data = pd.DataFrame([
            {
                'user_id': 'user1@company.com',
                'user_name': 'User One',
                'email': 'user1@company.com',
                'department': 'Engineering',
                'date': '2025-01-15',  # Same month, different day
                'feature_used': 'ChatGPT Messages',
                'usage_count': 150,  # Updated count
                'cost_usd': 60.0,
                'tool_source': 'ChatGPT',
                'file_source': 'upload2.csv'
            }
        ])
        
        # Process second upload
        success, message = self.processor.process_monthly_data(second_data, 'upload2.csv')
        self.assertTrue(success)
        
        # Verify superseding - should only have 1 record with new count
        all_data = self.db.get_all_data()
        self.assertEqual(len(all_data), 1, "Should have exactly 1 record after superseding")
        self.assertEqual(all_data.iloc[0]['usage_count'], 150, "Should have updated count")
        self.assertEqual(all_data.iloc[0]['file_source'], 'upload2.csv', "Should have new file source")
    
    def test_blueflame_superseding_single_user_single_month(self):
        """Test that BlueFlame re-upload replaces data for same user and month."""
        # First upload
        first_data = pd.DataFrame([
            {
                'user_id': 'user2@company.com',
                'user_name': 'User Two',
                'email': 'user2@company.com',
                'department': 'Sales',
                'date': '2025-02-01',
                'feature_used': 'BlueFlame Messages',
                'usage_count': 200,
                'cost_usd': 125.0,
                'tool_source': 'BlueFlame AI',
                'file_source': 'blueflame1.csv'
            }
        ])
        
        success, message = self.processor.process_monthly_data(first_data, 'blueflame1.csv')
        self.assertTrue(success)
        
        # Second upload - updated count
        second_data = pd.DataFrame([
            {
                'user_id': 'user2@company.com',
                'user_name': 'User Two',
                'email': 'user2@company.com',
                'department': 'Sales',
                'date': '2025-02-15',
                'feature_used': 'BlueFlame Messages',
                'usage_count': 250,
                'cost_usd': 125.0,
                'tool_source': 'BlueFlame AI',
                'file_source': 'blueflame2.csv'
            }
        ])
        
        success, message = self.processor.process_monthly_data(second_data, 'blueflame2.csv')
        self.assertTrue(success)
        
        # Verify superseding
        all_data = self.db.get_all_data()
        self.assertEqual(len(all_data), 1)
        self.assertEqual(all_data.iloc[0]['usage_count'], 250)
    
    def test_superseding_multiple_users_same_month(self):
        """Test superseding with multiple users in same month."""
        # First upload - 2 users in March
        first_data = pd.DataFrame([
            {
                'user_id': 'user1@company.com',
                'user_name': 'User One',
                'email': 'user1@company.com',
                'department': 'Engineering',
                'date': '2025-03-01',
                'feature_used': 'ChatGPT Messages',
                'usage_count': 100,
                'cost_usd': 60.0,
                'tool_source': 'ChatGPT',
                'file_source': 'upload1.csv'
            },
            {
                'user_id': 'user2@company.com',
                'user_name': 'User Two',
                'email': 'user2@company.com',
                'department': 'Sales',
                'date': '2025-03-01',
                'feature_used': 'ChatGPT Messages',
                'usage_count': 200,
                'cost_usd': 60.0,
                'tool_source': 'ChatGPT',
                'file_source': 'upload1.csv'
            }
        ])
        
        success, message = self.processor.process_monthly_data(first_data, 'upload1.csv')
        self.assertTrue(success)
        self.assertEqual(len(self.db.get_all_data()), 2)
        
        # Second upload - same users, updated counts
        second_data = pd.DataFrame([
            {
                'user_id': 'user1@company.com',
                'user_name': 'User One',
                'email': 'user1@company.com',
                'department': 'Engineering',
                'date': '2025-03-15',
                'feature_used': 'ChatGPT Messages',
                'usage_count': 150,
                'cost_usd': 60.0,
                'tool_source': 'ChatGPT',
                'file_source': 'upload2.csv'
            },
            {
                'user_id': 'user2@company.com',
                'user_name': 'User Two',
                'email': 'user2@company.com',
                'department': 'Sales',
                'date': '2025-03-20',
                'feature_used': 'ChatGPT Messages',
                'usage_count': 250,
                'cost_usd': 60.0,
                'tool_source': 'ChatGPT',
                'file_source': 'upload2.csv'
            }
        ])
        
        success, message = self.processor.process_monthly_data(second_data, 'upload2.csv')
        self.assertTrue(success)
        
        # Should still have 2 records with updated counts
        all_data = self.db.get_all_data()
        self.assertEqual(len(all_data), 2)
        
        user1_data = all_data[all_data['user_id'] == 'user1@company.com']
        user2_data = all_data[all_data['user_id'] == 'user2@company.com']
        
        self.assertEqual(user1_data.iloc[0]['usage_count'], 150)
        self.assertEqual(user2_data.iloc[0]['usage_count'], 250)
    
    def test_superseding_multiple_months(self):
        """Test superseding across multiple months."""
        # First upload - 2 months
        first_data = pd.DataFrame([
            {
                'user_id': 'user1@company.com',
                'user_name': 'User One',
                'email': 'user1@company.com',
                'department': 'Engineering',
                'date': '2025-01-01',
                'feature_used': 'ChatGPT Messages',
                'usage_count': 100,
                'cost_usd': 60.0,
                'tool_source': 'ChatGPT',
                'file_source': 'upload1.csv'
            },
            {
                'user_id': 'user1@company.com',
                'user_name': 'User One',
                'email': 'user1@company.com',
                'department': 'Engineering',
                'date': '2025-02-01',
                'feature_used': 'ChatGPT Messages',
                'usage_count': 200,
                'cost_usd': 60.0,
                'tool_source': 'ChatGPT',
                'file_source': 'upload1.csv'
            }
        ])
        
        success, message = self.processor.process_monthly_data(first_data, 'upload1.csv')
        self.assertTrue(success)
        self.assertEqual(len(self.db.get_all_data()), 2)
        
        # Second upload - updated January only
        second_data = pd.DataFrame([
            {
                'user_id': 'user1@company.com',
                'user_name': 'User One',
                'email': 'user1@company.com',
                'department': 'Engineering',
                'date': '2025-01-15',
                'feature_used': 'ChatGPT Messages',
                'usage_count': 150,
                'cost_usd': 60.0,
                'tool_source': 'ChatGPT',
                'file_source': 'upload2.csv'
            }
        ])
        
        success, message = self.processor.process_monthly_data(second_data, 'upload2.csv')
        self.assertTrue(success)
        
        # Should have 2 records: updated Jan + original Feb
        all_data = self.db.get_all_data()
        self.assertEqual(len(all_data), 2)
        
        jan_data = all_data[all_data['date'].str.startswith('2025-01')]
        feb_data = all_data[all_data['date'].str.startswith('2025-02')]
        
        self.assertEqual(len(jan_data), 1)
        self.assertEqual(jan_data.iloc[0]['usage_count'], 150)
        self.assertEqual(len(feb_data), 1)
        self.assertEqual(feb_data.iloc[0]['usage_count'], 200)
    
    def test_no_superseding_for_different_users(self):
        """Test that different users don't supersede each other."""
        # Upload user1 data
        user1_data = pd.DataFrame([
            {
                'user_id': 'user1@company.com',
                'user_name': 'User One',
                'email': 'user1@company.com',
                'department': 'Engineering',
                'date': '2025-01-01',
                'feature_used': 'ChatGPT Messages',
                'usage_count': 100,
                'cost_usd': 60.0,
                'tool_source': 'ChatGPT',
                'file_source': 'user1.csv'
            }
        ])
        
        success, message = self.processor.process_monthly_data(user1_data, 'user1.csv')
        self.assertTrue(success)
        
        # Upload user2 data for same month
        user2_data = pd.DataFrame([
            {
                'user_id': 'user2@company.com',
                'user_name': 'User Two',
                'email': 'user2@company.com',
                'department': 'Sales',
                'date': '2025-01-01',
                'feature_used': 'ChatGPT Messages',
                'usage_count': 200,
                'cost_usd': 60.0,
                'tool_source': 'ChatGPT',
                'file_source': 'user2.csv'
            }
        ])
        
        success, message = self.processor.process_monthly_data(user2_data, 'user2.csv')
        self.assertTrue(success)
        
        # Should have both records
        all_data = self.db.get_all_data()
        self.assertEqual(len(all_data), 2)
    
    def test_superseding_with_multiple_features(self):
        """Test superseding when multiple features are present."""
        # First upload - multiple features
        first_data = pd.DataFrame([
            {
                'user_id': 'user1@company.com',
                'user_name': 'User One',
                'email': 'user1@company.com',
                'department': 'Engineering',
                'date': '2025-01-01',
                'feature_used': 'ChatGPT Messages',
                'usage_count': 100,
                'cost_usd': 60.0,
                'tool_source': 'ChatGPT',
                'file_source': 'upload1.csv'
            },
            {
                'user_id': 'user1@company.com',
                'user_name': 'User One',
                'email': 'user1@company.com',
                'department': 'Engineering',
                'date': '2025-01-01',
                'feature_used': 'GPT Messages',
                'usage_count': 50,
                'cost_usd': 0.0,
                'tool_source': 'ChatGPT',
                'file_source': 'upload1.csv'
            }
        ])
        
        success, message = self.processor.process_monthly_data(first_data, 'upload1.csv')
        self.assertTrue(success)
        self.assertEqual(len(self.db.get_all_data()), 2)
        
        # Second upload - updated counts for both features
        second_data = pd.DataFrame([
            {
                'user_id': 'user1@company.com',
                'user_name': 'User One',
                'email': 'user1@company.com',
                'department': 'Engineering',
                'date': '2025-01-15',
                'feature_used': 'ChatGPT Messages',
                'usage_count': 150,
                'cost_usd': 60.0,
                'tool_source': 'ChatGPT',
                'file_source': 'upload2.csv'
            },
            {
                'user_id': 'user1@company.com',
                'user_name': 'User One',
                'email': 'user1@company.com',
                'department': 'Engineering',
                'date': '2025-01-15',
                'feature_used': 'GPT Messages',
                'usage_count': 75,
                'cost_usd': 0.0,
                'tool_source': 'ChatGPT',
                'file_source': 'upload2.csv'
            }
        ])
        
        success, message = self.processor.process_monthly_data(second_data, 'upload2.csv')
        self.assertTrue(success)
        
        # Should still have 2 records (one per feature) with updated counts
        all_data = self.db.get_all_data()
        self.assertEqual(len(all_data), 2)
        
        chatgpt_data = all_data[all_data['feature_used'] == 'ChatGPT Messages']
        gpt_data = all_data[all_data['feature_used'] == 'GPT Messages']
        
        self.assertEqual(chatgpt_data.iloc[0]['usage_count'], 150)
        self.assertEqual(gpt_data.iloc[0]['usage_count'], 75)


class TestDuplicateDetection(unittest.TestCase):
    """Test duplicate record detection after uploads."""
    
    def setUp(self):
        """Set up test database."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db = DatabaseManager(self.temp_db.name)
    
    def tearDown(self):
        """Clean up test database."""
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
    
    def test_no_duplicates_in_clean_data(self):
        """Test that clean data returns no duplicates."""
        # Insert non-duplicate data
        conn = sqlite3.connect(self.db.db_path)
        test_data = pd.DataFrame([
            {
                'user_id': 'user1@company.com',
                'user_name': 'User One',
                'email': 'user1@company.com',
                'department': 'Engineering',
                'date': '2025-01-01',
                'feature_used': 'ChatGPT Messages',
                'usage_count': 100,
                'cost_usd': 60.0,
                'tool_source': 'ChatGPT',
                'file_source': 'test.csv'
            },
            {
                'user_id': 'user2@company.com',
                'user_name': 'User Two',
                'email': 'user2@company.com',
                'department': 'Sales',
                'date': '2025-01-01',
                'feature_used': 'ChatGPT Messages',
                'usage_count': 200,
                'cost_usd': 60.0,
                'tool_source': 'ChatGPT',
                'file_source': 'test.csv'
            }
        ])
        test_data.to_sql('usage_metrics', conn, if_exists='append', index=False)
        conn.close()
        
        # Check for duplicates
        duplicates = self.db.detect_duplicates()
        self.assertTrue(duplicates.empty, "Should find no duplicates in clean data")
    
    def test_detect_exact_duplicates(self):
        """Test detection of exact duplicate records."""
        # Insert duplicate data
        conn = sqlite3.connect(self.db.db_path)
        test_data = pd.DataFrame([
            {
                'user_id': 'user1@company.com',
                'user_name': 'User One',
                'email': 'user1@company.com',
                'department': 'Engineering',
                'date': '2025-01-01',
                'feature_used': 'ChatGPT Messages',
                'usage_count': 100,
                'cost_usd': 60.0,
                'tool_source': 'ChatGPT',
                'file_source': 'test.csv'
            },
            {
                'user_id': 'user1@company.com',
                'user_name': 'User One',
                'email': 'user1@company.com',
                'department': 'Engineering',
                'date': '2025-01-01',
                'feature_used': 'ChatGPT Messages',
                'usage_count': 100,
                'cost_usd': 60.0,
                'tool_source': 'ChatGPT',
                'file_source': 'test.csv'
            }
        ])
        test_data.to_sql('usage_metrics', conn, if_exists='append', index=False)
        conn.close()
        
        # Check for duplicates
        duplicates = self.db.detect_duplicates()
        self.assertEqual(len(duplicates), 1, "Should detect 1 set of duplicates")
        self.assertEqual(duplicates.iloc[0]['duplicate_count'], 2, "Should have 2 duplicate records")


class TestSupersedingPreview(unittest.TestCase):
    """Test superseding preview functionality."""
    
    def setUp(self):
        """Set up test database with sample data."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db = DatabaseManager(self.temp_db.name)
        
        # Insert sample data
        conn = sqlite3.connect(self.db.db_path)
        test_data = pd.DataFrame([
            {
                'user_id': 'user1@company.com',
                'user_name': 'User One',
                'email': 'user1@company.com',
                'department': 'Engineering',
                'date': '2025-01-01',
                'feature_used': 'ChatGPT Messages',
                'usage_count': 100,
                'cost_usd': 60.0,
                'tool_source': 'ChatGPT',
                'file_source': 'old.csv'
            },
            {
                'user_id': 'user1@company.com',
                'user_name': 'User One',
                'email': 'user1@company.com',
                'department': 'Engineering',
                'date': '2025-02-01',
                'feature_used': 'ChatGPT Messages',
                'usage_count': 150,
                'cost_usd': 60.0,
                'tool_source': 'ChatGPT',
                'file_source': 'old.csv'
            },
            {
                'user_id': 'user2@company.com',
                'user_name': 'User Two',
                'email': 'user2@company.com',
                'department': 'Sales',
                'date': '2025-01-01',
                'feature_used': 'ChatGPT Messages',
                'usage_count': 200,
                'cost_usd': 60.0,
                'tool_source': 'ChatGPT',
                'file_source': 'old.csv'
            }
        ])
        test_data.to_sql('usage_metrics', conn, if_exists='append', index=False)
        conn.close()
    
    def tearDown(self):
        """Clean up test database."""
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
    
    def test_preview_single_user_single_month(self):
        """Test preview for single user and month."""
        preview = self.db.get_superseding_preview(
            'ChatGPT',
            ['2025-01'],
            ['user1@company.com']
        )
        
        self.assertEqual(preview['total_records'], 1, "Should find 1 record to supersede")
        self.assertEqual(preview['affected_users'], 1, "Should affect 1 user")
    
    def test_preview_multiple_months(self):
        """Test preview for multiple months."""
        preview = self.db.get_superseding_preview(
            'ChatGPT',
            ['2025-01', '2025-02'],
            ['user1@company.com']
        )
        
        self.assertEqual(preview['total_records'], 2, "Should find 2 records to supersede")
        self.assertEqual(preview['affected_users'], 1, "Should affect 1 user")
    
    def test_preview_multiple_users(self):
        """Test preview for multiple users."""
        preview = self.db.get_superseding_preview(
            'ChatGPT',
            ['2025-01'],
            ['user1@company.com', 'user2@company.com']
        )
        
        self.assertEqual(preview['total_records'], 2, "Should find 2 records to supersede")
        self.assertEqual(preview['affected_users'], 2, "Should affect 2 users")
    
    def test_preview_no_matching_records(self):
        """Test preview when no matching records exist."""
        preview = self.db.get_superseding_preview(
            'ChatGPT',
            ['2025-12'],  # Month with no data
            ['user1@company.com']
        )
        
        self.assertEqual(preview['total_records'], 0, "Should find 0 records to supersede")


if __name__ == '__main__':
    unittest.main()
