#!/usr/bin/env python3
"""
Error Reporting and Classification Tests
Tests for enhanced error classification and reporting for Auto Issue Processor
"""

import asyncio
import pytest
import time
import json
from unittest.mock import Mock, AsyncMock, patch, mock_open
from datetime import datetime

from libs.auto_issue_processor_error_handling import (
    ErrorReport,
    ErrorReporter,
    ErrorCategory,
    ErrorSeverity,
    ErrorPattern,
    ErrorAnalytics
)

class TestErrorReport:
    """Test suite for Error Report data structure"""
    
    def test_error_report_creation(self):
        """Test creating an error report"""
        error = ValueError("Test error")
        report = ErrorReport(
            error_id="ERR001",
            timestamp=datetime.now(),
            error_type="ValueError",
            error_message="Test error",
            error_category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.HIGH,
            operation="test_operation",
            issue_number=123,
            stack_trace="test stack trace",
            context={"key": "value"},

            recovery_successful=False,
            recovery_action="retry"
        )
        
        assert report.error_id == "ERR001"
        assert report.error_type == "ValueError"
        assert report.error_category == ErrorCategory.VALIDATION
        assert report.severity == ErrorSeverity.HIGH
        assert report.issue_number == 123
    
    def test_error_report_to_dict(self):
        """Test converting error report to dictionary"""
        report = ErrorReport(
            error_id="ERR001",
            timestamp=datetime.now(),
            error_type="ValueError",
            error_message="Test error",
            error_category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.HIGH,
            operation="test_operation"
        )
        
        report_dict = report.to_dict()
        assert isinstance(report_dict, dict)
        assert report_dict["error_id"] == "ERR001"
        assert report_dict["error_type"] == "ValueError"
        assert report_dict["error_category"] == "validation"
        assert report_dict["severity"] == "high"

class TestErrorReporter:
    """Test suite for Error Reporter"""
    
    @pytest.fixture
    def error_reporter(self):
        """Create an error reporter instance"""
        return ErrorReporter(report_dir="/tmp/test_reports")
    
    @pytest.mark.asyncio
    async def test_generate_error_id(self, error_reporter):
        """Test error ID generation"""
        error_id1 = error_reporter.generate_error_id()
        error_id2 = error_reporter.generate_error_id()
        
        assert error_id1.startswith("ERR-")
        assert error_id2.startswith("ERR-")
        assert error_id1 != error_id2
    
    @pytest.mark.asyncio
    async def test_classify_error(self, error_reporter):
        """Test error classification"""
        # GitHub API error
        github_error = Exception("API rate limit exceeded")
        category, severity = error_reporter.classify_error(github_error, "github_api_call")
        assert category == ErrorCategory.GITHUB_API
        assert severity == ErrorSeverity.HIGH
        
        # Network error
        network_error = ConnectionError("Connection refused")
        category, severity = error_reporter.classify_error(network_error, "network_request")
        assert category == ErrorCategory.NETWORK
        assert severity == ErrorSeverity.MEDIUM
        
        # Validation error
        validation_error = ValueError("Invalid input")
        category, severity = error_reporter.classify_error(validation_error, "validate_input")
        assert category == ErrorCategory.VALIDATION
        assert severity == ErrorSeverity.LOW
    
    @pytest.mark.asyncio
    async def test_create_report(self, error_reporter):
        """Test creating an error report"""
        error = ValueError("Test error")
        report = await error_reporter.create_report(
            error=error,
            operation="test_operation",
            issue_number=123,
            context={"key": "value"}
        )
        
        assert report.error_type == "ValueError"
        assert report.error_message == "Test error"
        assert report.operation == "test_operation"
        assert report.issue_number == 123
        assert report.context == {"key": "value"}
    
    @pytest.mark.asyncio
    async def test_save_report(self, error_reporter):
        """Test saving error report to file"""
        report = ErrorReport(
            error_id="ERR001",
            timestamp=datetime.now(),
            error_type="ValueError",
            error_message="Test error",
            error_category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.HIGH,
            operation="test_operation"
        )
        
        with patch("builtins.open", mock_open()) as mock_file:
            await error_reporter.save_report(report)
            mock_file.assert_called_once()
            # Verify JSON was written
            handle = mock_file()
            written_data = ''.join(call.args[0] for call in handle.write.call_args_list)
            assert "ERR001" in written_data
    
    @pytest.mark.asyncio
    async def test_get_error_patterns(self, error_reporter):
        """Test extracting error patterns"""
        # Add some error reports
        errors = [
            ValueError("Invalid input"),
            ValueError("Invalid input"),
            ConnectionError("Connection refused"),
            ConnectionError("Connection refused"),
            ConnectionError("Connection refused")
        ]
        
        for error in errors:
            report = await error_reporter.create_report(error, "test_op")
        
        patterns = await error_reporter.get_error_patterns()
        
        assert len(patterns) == 2
        assert any(p.error_type == "ValueError" and p.count == 2 for p in patterns)
        assert any(p.error_type == "ConnectionError" and p.count == 3 for p in patterns)
    
    @pytest.mark.asyncio
    async def test_get_error_trends(self, error_reporter):
        """Test analyzing error trends"""
        # Add error reports over time
        base_time = datetime.now()
        
        for i in range(5):
            report = ErrorReport(
                error_id=f"ERR{i}",
                timestamp=base_time,
                error_type="TestError",
                error_message="Test",
                error_category=ErrorCategory.SYSTEM,
                severity=ErrorSeverity.HIGH,
                operation="test_op"
            )
            error_reporter.error_history.append(report)
        
        trends = await error_reporter.get_error_trends(hours=1)
        
        assert trends["total_errors"] == 5
        assert trends["errors_by_category"]["system"] == 5
        assert trends["errors_by_severity"]["high"] == 5
    
    @pytest.mark.asyncio
    async def test_generate_summary_report(self, error_reporter):
        """Test generating summary report"""
        # Add various error reports
        errors = [
            (ValueError("Test"), ErrorCategory.VALIDATION, ErrorSeverity.LOW),
            (ConnectionError("Test"), ErrorCategory.NETWORK, ErrorSeverity.MEDIUM),
            (Exception("API error"), ErrorCategory.GITHUB_API, ErrorSeverity.HIGH)
        ]
        
        for error, category, severity in errors:
            report = ErrorReport(
                error_id=error_reporter.generate_error_id(),
                timestamp=datetime.now(),
                error_type=type(error).__name__,
                error_message=str(error),
                error_category=category,
                severity=severity,
                operation="test_op",

                recovery_successful=False
            )
            error_reporter.error_history.append(report)
        
        summary = await error_reporter.generate_summary_report()
        
        assert summary["total_errors"] == 3
        assert summary["unique_error_types"] == 3
        assert summary["recovery_success_rate"] == 0.0
        assert len(summary["top_errors"]) > 0
        assert len(summary["recommendations"]) > 0

class TestErrorAnalytics:
    """Test suite for Error Analytics"""
    
    @pytest.fixture
    def error_analytics(self):
        """Create an error analytics instance"""
        return ErrorAnalytics()
    
    @pytest.mark.asyncio
    async def test_calculate_mttr(self, error_analytics):
        """Test Mean Time To Recovery calculation"""
        recovery_times = [60, 120, 180, 240, 300]  # seconds
        
        for time in recovery_times:
            await error_analytics.record_recovery(
                error_id=f"ERR{time}",
                recovery_time=time
            )
        
        mttr = await error_analytics.calculate_mttr()
        assert mttr == 180  # average of recovery times
    
    @pytest.mark.asyncio
    async def test_identify_error_clusters(self, error_analytics):
        """Test identifying error clusters"""
        # Add clustered errors
        base_time = datetime.now()
        
        # Cluster 1: Multiple errors in short time
        for i in range(5):
            await error_analytics.add_error(
                error_type="NetworkError",
                timestamp=base_time,
                operation="api_call"
            )
        
        clusters = await error_analytics.identify_error_clusters(
            time_window_minutes=5,
            min_cluster_size=3
        )
        
        assert len(clusters) >= 1
        assert clusters[0]["error_count"] >= 3
    
    @pytest.mark.asyncio
    async def test_predict_error_likelihood(self, error_analytics):
        """Test error likelihood prediction"""
        # Add historical error data
        for i in range(10):
            await error_analytics.add_error(
                error_type="APIError",
                timestamp=datetime.now(),
                operation="github_api_call"
            )
        
        likelihood = await error_analytics.predict_error_likelihood(
            operation="github_api_call",
            error_type="APIError"
        )
        
        assert 0 <= likelihood <= 1
        assert likelihood > 0  # Should have some likelihood given the history
    
    @pytest.mark.asyncio
    async def test_get_error_correlations(self, error_analytics):
        """Test finding error correlations"""
        # Add correlated errors
        for i in range(5):
            await error_analytics.add_error("NetworkError", datetime.now(), "api_call")
            await error_analytics.add_error("TimeoutError", datetime.now(), "api_call")
        
        correlations = await error_analytics.get_error_correlations()
        
        assert len(correlations) > 0
        # NetworkError and TimeoutError should be correlated
        assert any(
            (c["error_type_1"] == "NetworkError" and c["error_type_2"] == "TimeoutError") or
            (c["error_type_1"] == "TimeoutError" and c["error_type_2"] == "NetworkError")
            for c in correlations
        )