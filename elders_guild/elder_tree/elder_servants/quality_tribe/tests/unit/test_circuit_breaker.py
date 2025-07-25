#!/usr/bin/env python3
"""
Circuit Breaker Pattern Tests
Tests for the circuit breaker implementation for Auto Issue Processor
"""

import asyncio
import pytest
import time
from unittest.mock import Mock, AsyncMock
from datetime import datetime, timedelta

from elders_guild.elder_tree.auto_issue_processor_error_handling import (
    CircuitBreaker,
    CircuitState,
    CircuitBreakerError,
    CircuitBreakerOpenError
)


class TestCircuitBreaker:
    """Test suite for Circuit Breaker implementation"""
    
    @pytest.fixture
    def circuit_breaker(self):
        """Create a circuit breaker instance for testing"""
        return CircuitBreaker(
            failure_threshold=3,
            recovery_timeout=1.0,  # 1 second for faster tests
            expected_exception=Exception
        )
    
    @pytest.mark.asyncio
    async def test_initial_state_is_closed(self, circuit_breaker):
        """Test that circuit breaker starts in closed state"""
        assert circuit_breaker.state == CircuitState.CLOSED
        assert circuit_breaker.failure_count == 0
        assert circuit_breaker.last_failure_time is None
    
    @pytest.mark.asyncio
    async def test_successful_call_in_closed_state(self, circuit_breaker):
        """Test successful function call when circuit is closed"""
        async def success_func():
            return "success"
        
        result = await circuit_breaker.call(success_func)
        assert result == "success"
        assert circuit_breaker.state == CircuitState.CLOSED
        assert circuit_breaker.failure_count == 0
    
    @pytest.mark.asyncio
    async def test_failure_increments_counter(self, circuit_breaker):
        """Test that failures increment the failure counter"""
        async def failing_func():
            raise Exception("Test failure")
        
        with pytest.raises(Exception):
            await circuit_breaker.call(failing_func)
        
        assert circuit_breaker.failure_count == 1
        assert circuit_breaker.state == CircuitState.CLOSED
    
    @pytest.mark.asyncio
    async def test_circuit_opens_after_threshold(self, circuit_breaker):
        """Test that circuit opens after reaching failure threshold"""
        async def failing_func():
            raise Exception("Test failure")
        
        # Fail 3 times to reach threshold
        for _ in range(3):
            with pytest.raises(Exception):
                await circuit_breaker.call(failing_func)
        
        assert circuit_breaker.state == CircuitState.OPEN
        assert circuit_breaker.failure_count == 3
    
    @pytest.mark.asyncio
    async def test_open_circuit_rejects_calls(self, circuit_breaker):
        """Test that open circuit rejects calls immediately"""
        async def failing_func():
            raise Exception("Test failure")
        
        # Open the circuit
        for _ in range(3):
            with pytest.raises(Exception):
                await circuit_breaker.call(failing_func)
        
        # Now circuit should be open
        async def success_func():
            return "success"
        
        with pytest.raises(CircuitBreakerOpenError):
            await circuit_breaker.call(success_func)
    
    @pytest.mark.asyncio
    async def test_half_open_state_after_timeout(self, circuit_breaker):
        """Test transition to half-open state after recovery timeout"""
        async def failing_func():
            raise Exception("Test failure")
        
        # Open the circuit
        for _ in range(3):
            with pytest.raises(Exception):
                await circuit_breaker.call(failing_func)
        
        # Wait for recovery timeout
        await asyncio.sleep(1.1)
        
        # Circuit should now be half-open
        assert circuit_breaker.state == CircuitState.HALF_OPEN
    
    @pytest.mark.asyncio
    async def test_half_open_success_closes_circuit(self, circuit_breaker):
        """Test that successful call in half-open state closes the circuit"""
        async def failing_func():
            raise Exception("Test failure")
        
        # Open the circuit
        for _ in range(3):
            with pytest.raises(Exception):
                await circuit_breaker.call(failing_func)
        
        # Wait for recovery timeout
        await asyncio.sleep(1.1)
        
        # Successful call should close the circuit
        async def success_func():
            return "success"
        
        result = await circuit_breaker.call(success_func)
        assert result == "success"
        assert circuit_breaker.state == CircuitState.CLOSED
        assert circuit_breaker.failure_count == 0
    
    @pytest.mark.asyncio
    async def test_half_open_failure_reopens_circuit(self, circuit_breaker):
        """Test that failure in half-open state reopens the circuit"""
        async def failing_func():
            raise Exception("Test failure")
        
        # Open the circuit
        for _ in range(3):
            with pytest.raises(Exception):
                await circuit_breaker.call(failing_func)
        
        # Wait for recovery timeout
        await asyncio.sleep(1.1)
        
        # Failure should reopen the circuit
        with pytest.raises(Exception):
            await circuit_breaker.call(failing_func)
        
        assert circuit_breaker.state == CircuitState.OPEN
    
    @pytest.mark.asyncio
    async def test_decorator_pattern(self):
        """Test circuit breaker as a decorator"""
        cb = CircuitBreaker(failure_threshold=2, recovery_timeout=0.5)
        call_count = 0
        
        @cb.decorator
        async def protected_function(should_fail=False):
            nonlocal call_count
            """protected_functionメソッド"""
            call_count += 1
            if should_fail:
                raise Exception("Deliberate failure")
            return "success"
        
        # Successful calls
        result = await protected_function()
        assert result == "success"
        
        # Fail twice to open circuit
        for _ in range(2):
            with pytest.raises(Exception):
                await protected_function(should_fail=True)
        
        # Circuit should be open
        with pytest.raises(CircuitBreakerOpenError):
            await protected_function()
        
        # Verify function wasn't called when circuit was open
        assert call_count == 3  # 1 success + 2 failures
    
    @pytest.mark.asyncio
    async def test_excluded_exceptions(self):
        """Test that excluded exceptions don't trip the circuit"""
        class IgnoredException(Exception):
            """IgnoredExceptionクラス"""
            pass
        
        cb = CircuitBreaker(
            failure_threshold=2,
            recovery_timeout=1.0,
            expected_exception=Exception,
            exclude_exceptions=[IgnoredException]
        )
        
        async def func_with_ignored_exception():
            raise IgnoredException("This should be ignored")
        
        # This exception should not increment failure count
        with pytest.raises(IgnoredException):
            await cb.call(func_with_ignored_exception)
        
        assert cb.failure_count == 0
        assert cb.state == CircuitState.CLOSED
    
    @pytest.mark.asyncio
    async def test_success_callback(self, circuit_breaker):
        """Test success callback is called on successful execution"""
        callback_called = False
        callback_result = None
        
        def on_success(result):
            nonlocal callback_called, callback_result
            callback_called = True
            callback_result = result
        
        circuit_breaker.on_success = on_success
        
        async def success_func():
            return "test_result"
        
        result = await circuit_breaker.call(success_func)
        
        assert callback_called
        assert callback_result == "test_result"
    
    @pytest.mark.asyncio
    async def test_failure_callback(self, circuit_breaker):
        """Test failure callback is called on failed execution"""
        callback_called = False
        callback_exception = None
        
        def on_failure(exception):
            nonlocal callback_called, callback_exception
            callback_called = True
            callback_exception = exception
        
        circuit_breaker.on_failure = on_failure
        
        async def failing_func():
            raise ValueError("Test error")
        
        with pytest.raises(ValueError):
            await circuit_breaker.call(failing_func)
        
        assert callback_called
        assert isinstance(callback_exception, ValueError)
        assert str(callback_exception) == "Test error"
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_metrics(self, circuit_breaker):
        """Test circuit breaker metrics collection"""
        async def success_func():
            return "success"
        
        async def failing_func():
            raise Exception("failure")
        
        # Execute some calls
        await circuit_breaker.call(success_func)
        await circuit_breaker.call(success_func)
        
        with pytest.raises(Exception):
            await circuit_breaker.call(failing_func)
        
        metrics = circuit_breaker.get_metrics()
        
        assert metrics["total_calls"] == 3
        assert metrics["successful_calls"] == 2
        assert metrics["failed_calls"] == 1
        assert metrics["success_rate"] == 2/3
        assert metrics["current_state"] == CircuitState.CLOSED.value
        assert metrics["failure_count"] == 1