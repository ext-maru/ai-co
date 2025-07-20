import pytest
import unittest.mock as mock
from pathlib import Path
import sys

from generated import GeneratedImplementation, DataProcessor, ConfigurationManager


class TestGeneratedImplementation:
    """Unit tests for GeneratedImplementation"""

    def setup_method(self):
        """Setup test environment"""
        self.test_instance = GeneratedImplementation() if GeneratedImplementation else None

    def teardown_method(self):
        """Cleanup after test"""
        self.test_instance = None

    def test_initialization(self):
        """Test class initialization"""
        assert self.test_instance is not None
        assert self.test_instance.initialized is True
        assert isinstance(self.test_instance.config, dict)
        assert isinstance(self.test_instance.data_store, dict)
        
        # Test initialization with config
        config = {"debug": True, "timeout": 30}
        instance_with_config = GeneratedImplementation(config)
        assert instance_with_config.config == config

    def test_basic_functionality(self):
        """Test basic functionality"""
        # Test data processing
        result = self.test_instance.process_data(42)
        assert result["original"] == 42
        assert result["processed"] is True
        assert result["squared"] == 1764
        assert result["sqrt"] == pytest.approx(6.48, rel=1e-2)
        
        # Test string processing
        result = self.test_instance.process_data("hello world")
        assert result["length"] == 11
        assert result["uppercase"] == "HELLO WORLD"
        assert result["words"] == ["hello", "world"]
        
        # Test data storage
        assert self.test_instance.store_data("test_key", "test_value") is True
        assert self.test_instance.retrieve_data("test_key") == "test_value"

    def test_edge_cases(self):
        """Test edge cases"""
        # Test None input
        with pytest.raises(ValueError, match="Data cannot be None"):
            self.test_instance.process_data(None)
            
        # Test empty string key
        with pytest.raises(ValueError, match="Key must be a non-empty string"):
            self.test_instance.store_data("", "value")
            
        # Test non-existent key retrieval
        assert self.test_instance.retrieve_data("non_existent") is None
        
        # Test negative number square root
        result = self.test_instance.process_data(-25)
        assert result["squared"] == 625
        assert result["sqrt"] is None  # Negative numbers return None for sqrt
        
        # Test empty collections
        result = self.test_instance.process_data([])
        assert result["count"] == 0
        assert result["sum"] == 0

    def test_error_handling(self):
        """Test error handling"""
        # Test invalid data storage key
        with pytest.raises(ValueError):
            self.test_instance.store_data(None, "value")
            
        with pytest.raises(ValueError):
            self.test_instance.store_data(123, "value")  # Non-string key
            
        # Test data processing with None
        with pytest.raises(ValueError):
            self.test_instance.process_data(None)
            
        # Test input validation with invalid criteria
        valid = self.test_instance.validate_input(50, {"type": str})
        assert valid is False  # Number vs string type mismatch
        
        valid = self.test_instance.validate_input(5, {"min": 10})
        assert valid is False  # Below minimum

    @pytest.mark.parametrize("input_data,expected_squared", [
        (1, 1),
        (2, 4),
        (3, 9),
        (10, 100),
        (-5, 25),
    ])
    def test_parametrized_number_processing(self, input_data, expected_squared):
        """Test number processing with multiple inputs"""
        result = self.test_instance.process_data(input_data)
        assert result["squared"] == expected_squared
        assert result["original"] == input_data
        assert result["processed"] is True
        
    @pytest.mark.parametrize("text,expected_length,expected_words", [
        ("hello", 5, ["hello"]),
        ("hello world", 11, ["hello", "world"]),
        ("", 0, []),
        ("a b c d", 7, ["a", "b", "c", "d"]),
    ])
    def test_parametrized_string_processing(self, text, expected_length, expected_words):
        """Test string processing with multiple inputs"""
        result = self.test_instance.process_data(text)
        assert result["length"] == expected_length
        assert result["words"] == expected_words
        assert result["uppercase"] == text.upper()


class TestDataProcessor:
    """Unit tests for DataProcessor"""

    def setup_method(self):
        """Setup test environment"""
        self.processor = DataProcessor()

    def test_transform_list_identity(self):
        """Test identity transformation"""
        data = [1, 2, 3, 4, 5]
        result = DataProcessor.transform_list(data, "identity")
        assert result == data
        assert result is not data  # Should be a copy

    def test_transform_list_reverse(self):
        """Test reverse transformation"""
        data = [1, 2, 3, 4, 5]
        result = DataProcessor.transform_list(data, "reverse")
        assert result == [5, 4, 3, 2, 1]

    def test_transform_list_sort(self):
        """Test sort transformation"""
        data = [3, 1, 4, 1, 5]
        result = DataProcessor.transform_list(data, "sort")
        assert result == [1, 1, 3, 4, 5]

    def test_transform_list_unique(self):
        """Test unique transformation"""
        data = [1, 2, 2, 3, 3, 3, 4]
        result = DataProcessor.transform_list(data, "unique")
        assert result == [1, 2, 3, 4]

    def test_transform_list_invalid_operation(self):
        """Test invalid operation"""
        with pytest.raises(ValueError, match="Unknown operation"):
            DataProcessor.transform_list([1, 2, 3], "invalid")

    def test_transform_list_non_list_input(self):
        """Test non-list input"""
        with pytest.raises(TypeError, match="Input must be a list"):
            DataProcessor.transform_list("not a list", "identity")

    def test_filter_data(self):
        """Test data filtering"""
        data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        
        # Filter even numbers
        result = DataProcessor.filter_data(data, lambda x: x % 2 == 0)
        assert result == [2, 4, 6, 8, 10]
        
        # Filter numbers greater than 5
        result = DataProcessor.filter_data(data, lambda x: x > 5)
        assert result == [6, 7, 8, 9, 10]

    def test_filter_data_invalid_predicate(self):
        """Test invalid predicate"""
        with pytest.raises(TypeError, match="Predicate must be callable"):
            DataProcessor.filter_data([1, 2, 3], "not callable")


class TestConfigurationManager:
    """Unit tests for ConfigurationManager"""

    def setup_method(self):
        """Setup test environment"""
        self.config_manager = ConfigurationManager()

    def test_initialization(self):
        """Test initialization"""
        assert isinstance(self.config_manager.settings, dict)
        assert len(self.config_manager.settings) == 0

    def test_load_config_dict(self):
        """Test loading config from dictionary"""
        config_data = {"debug": True, "timeout": 30, "retries": 3}
        result = self.config_manager.load_config(config_data)
        
        assert result is True
        assert self.config_manager.settings == config_data

    def test_load_config_json_string(self):
        """Test loading config from JSON string"""
        config_json = '{"debug": false, "timeout": 60, "host": "localhost"}'
        result = self.config_manager.load_config(config_json)
        
        assert result is True
        assert self.config_manager.settings["debug"] is False
        assert self.config_manager.settings["timeout"] == 60
        assert self.config_manager.settings["host"] == "localhost"

    def test_load_config_invalid_json(self):
        """Test loading invalid JSON"""
        with pytest.raises(ValueError, match="Invalid configuration data"):
            self.config_manager.load_config('{"invalid": json}')

    def test_load_config_invalid_type(self):
        """Test loading config with invalid type"""
        with pytest.raises(ValueError, match="Invalid configuration data"):
            self.config_manager.load_config(123)

    def test_get_setting(self):
        """Test getting settings"""
        self.config_manager.settings = {"debug": True, "timeout": 30}
        
        assert self.config_manager.get_setting("debug") is True
        assert self.config_manager.get_setting("timeout") == 30
        assert self.config_manager.get_setting("nonexistent") is None
        assert self.config_manager.get_setting("nonexistent", "default") == "default"

    def test_set_setting(self):
        """Test setting configuration values"""
        self.config_manager.set_setting("new_setting", "new_value")
        assert self.config_manager.get_setting("new_setting") == "new_value"

    def test_export_config(self):
        """Test exporting configuration"""
        self.config_manager.settings = {"debug": True, "timeout": 30}
        exported = self.config_manager.export_config()
        
        # Should be valid JSON
        import json
        parsed = json.loads(exported)
        assert parsed == {"debug": True, "timeout": 30}
