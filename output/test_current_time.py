import unittest
from datetime import datetime
import re
import time
from unittest.mock import patch
from current_time import display_current_time

class TestCurrentTime(unittest.TestCase):
    
    def test_display_current_time_format(self):
        """Test that display_current_time returns the correct format"""
        result = display_current_time()
        
        # Test format: YYYY-MM-DD HH:MM:SS
        pattern = r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$'
        self.assertIsNotNone(re.match(pattern, result), 
                           f"Time format should be YYYY-MM-DD HH:MM:SS, got: {result}")
    
    def test_display_current_time_returns_string(self):
        """Test that display_current_time returns a string"""
        result = display_current_time()
        self.assertIsInstance(result, str)
    
    def test_display_current_time_recent(self):
        """Test that display_current_time returns a recent time"""
        before_call = datetime.now()
        result = display_current_time()
        after_call = datetime.now()
        
        # Parse the returned time
        result_time = datetime.strptime(result, "%Y-%m-%d %H:%M:%S")
        
        # Check that the returned time is between before and after the call
        self.assertGreaterEqual(result_time, before_call.replace(microsecond=0))
        self.assertLessEqual(result_time, after_call.replace(microsecond=0))
    
    def test_display_current_time_consistency(self):
        """Test that multiple calls return consistent results within a second"""
        results = []
        for _ in range(5):
            results.append(display_current_time())
            time.sleep(0.1)
        
        # All results should have valid format
        for result in results:
            pattern = r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$'
            self.assertIsNotNone(re.match(pattern, result))
    
    def test_display_current_time_date_components(self):
        """Test that the date components are valid"""
        result = display_current_time()
        result_time = datetime.strptime(result, "%Y-%m-%d %H:%M:%S")
        
        # Check year is reasonable (current year)
        current_year = datetime.now().year
        self.assertEqual(result_time.year, current_year)
        
        # Check month is valid (1-12)
        self.assertGreaterEqual(result_time.month, 1)
        self.assertLessEqual(result_time.month, 12)
        
        # Check day is valid (1-31)
        self.assertGreaterEqual(result_time.day, 1)
        self.assertLessEqual(result_time.day, 31)
        
        # Check hour is valid (0-23)
        self.assertGreaterEqual(result_time.hour, 0)
        self.assertLessEqual(result_time.hour, 23)
        
        # Check minute is valid (0-59)
        self.assertGreaterEqual(result_time.minute, 0)
        self.assertLessEqual(result_time.minute, 59)
        
        # Check second is valid (0-59)
        self.assertGreaterEqual(result_time.second, 0)
        self.assertLessEqual(result_time.second, 59)
    
    @patch('current_time.datetime')
    def test_display_current_time_mocked(self, mock_datetime):
        """Test display_current_time with mocked datetime"""
        # Mock a specific datetime
        mock_time = datetime(2024, 7, 1, 15, 30, 45)
        mock_datetime.now.return_value = mock_time
        mock_datetime.strftime = datetime.strftime
        
        result = display_current_time()
        expected = "2024-07-01 15:30:45"
        self.assertEqual(result, expected)
    
    def test_display_current_time_no_exception(self):
        """Test that display_current_time doesn't raise any exceptions"""
        try:
            result = display_current_time()
            self.assertIsNotNone(result)
        except Exception as e:
            self.fail(f"display_current_time raised an exception: {e}")
    
    def test_display_current_time_length(self):
        """Test that display_current_time returns string of expected length"""
        result = display_current_time()
        # Format "YYYY-MM-DD HH:MM:SS" should be exactly 19 characters
        self.assertEqual(len(result), 19)

if __name__ == "__main__":
    unittest.main()