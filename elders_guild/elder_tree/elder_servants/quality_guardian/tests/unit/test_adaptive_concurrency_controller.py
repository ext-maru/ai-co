"""
Test suite for Adaptive Concurrency Controller
Phase 2 of Issue #192 - Dynamic parallelism adjustment
"""
import pytest
import asyncio
import time
from unittest.mock import Mock, patch, MagicMock
import psutil
from datetime import datetime, timedelta

from libs.adaptive_concurrency_controller import (
    AdaptiveConcurrencyController,
    ConcurrencyMetrics,
    ScalingDecision,
    ResourceMonitor,
    MLPredictor
)

class TestAdaptiveConcurrencyController:
    """Test suite for adaptive concurrency control"""
    
    @pytest.fixture
    def controller(self):
        """Create controller instance"""
        return AdaptiveConcurrencyController(
            min_workers=1,
            max_workers=10,
            target_cpu_percent=70,
            target_memory_percent=80
        )
    
    def test_initialization(self, controller):
        """Test controller initialization"""
        assert controller.min_workers == 1
        assert controller.max_workers == 10
        assert controller.current_workers == 1
        assert controller.target_cpu_percent == 70
        assert controller.target_memory_percent == 80
        assert controller.scaling_history == []
    
    def test_get_current_metrics(self, controller):
        """Test current system metrics retrieval"""
        metrics = controller.get_current_metrics()
        
        assert isinstance(metrics, ConcurrencyMetrics)
        assert 0 <= metrics.cpu_percent <= 100
        assert 0 <= metrics.memory_percent <= 100
        assert metrics.active_workers >= 0
        assert metrics.queue_size >= 0
        assert metrics.avg_processing_time >= 0
    
    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    def test_should_scale_up(self, mock_memory, mock_cpu, controller):
        """Test scale up decision logic"""
        # High CPU usage scenario
        mock_cpu.return_value = 85.0
        mock_memory.return_value = Mock(percent=60.0)
        
        controller.current_workers = 5  # Set current workers
        
        metrics = ConcurrencyMetrics(
            cpu_percent=85.0,
            memory_percent=60.0,
            active_workers=5,
            queue_size=100,
            avg_processing_time=3.5
        )
        
        decision = controller.should_scale_up(metrics)
        assert decision.should_scale is True
        assert decision.direction == "up"
        assert "High CPU usage" in decision.reason
        # With multiple triggers, balanced strategy adds 2 workers
        assert decision.new_worker_count == 7
    
    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    def test_should_scale_down(self, mock_memory, mock_cpu, controller):
        """Test scale down decision logic"""
        # Low resource usage scenario
        mock_cpu.return_value = 30.0
        mock_memory.return_value = Mock(percent=40.0)
        
        controller.current_workers = 5
        metrics = ConcurrencyMetrics(
            cpu_percent=30.0,
            memory_percent=40.0,
            active_workers=5,
            queue_size=10,
            avg_processing_time=1.0
        )
        
        decision = controller.should_scale_down(metrics)
        assert decision.should_scale is True
        assert decision.direction == "down"
        assert decision.reason == "Low resource utilization"
        assert decision.new_worker_count == 4
    
    def test_apply_scaling_decision(self, controller):
        """Test applying scaling decisions"""
        decision = ScalingDecision(
            should_scale=True,
            direction="up",
            new_worker_count=3,
            reason="Test scaling"
        )
        
        controller.apply_scaling_decision(decision)
        
        assert controller.current_workers == 3
        assert len(controller.scaling_history) == 1
        assert controller.scaling_history[0]['direction'] == "up"
        assert controller.scaling_history[0]['new_count'] == 3
    
    def test_max_workers_limit(self, controller):
        """Test max workers boundary"""
        controller.current_workers = 10
        
        metrics = ConcurrencyMetrics(
            cpu_percent=90.0,
            memory_percent=85.0,
            active_workers=10,
            queue_size=200,
            avg_processing_time=5.0
        )
        
        decision = controller.should_scale_up(metrics)
        assert decision.should_scale is False
        assert decision.reason == "Already at max workers"
    
    def test_min_workers_limit(self, controller):
        """Test min workers boundary"""
        controller.current_workers = 1
        
        metrics = ConcurrencyMetrics(
            cpu_percent=10.0,
            memory_percent=20.0,
            active_workers=1,
            queue_size=0,
            avg_processing_time=0.5
        )
        
        decision = controller.should_scale_down(metrics)
        assert decision.should_scale is False
        assert decision.reason == "Already at min workers"
    
    def test_scaling_cooldown(self, controller):
        """Test scaling cooldown period"""
        # Apply initial scaling
        decision = ScalingDecision(True, "up", 3, "Test")
        controller.apply_scaling_decision(decision)
        
        # Try to scale again immediately
        metrics = ConcurrencyMetrics(90.0, 85.0, 3, 100, 4.0)
        decision = controller.should_scale_up(metrics)
        
        assert decision.should_scale is False
        assert decision.reason == "In cooldown period"
    
    @pytest.mark.asyncio
    async def test_auto_adjust_loop(self, controller):
        """Test automatic adjustment loop"""
        controller.adjustment_interval = 0.1  # Fast for testing
        
        with patch.object(controller, 'get_current_metrics') as mock_metrics:
            with patch.object(controller, 'apply_scaling_decision') as mock_apply:
                mock_metrics.return_value = ConcurrencyMetrics(
                    cpu_percent=85.0,
                    memory_percent=70.0,
                    active_workers=2,
                    queue_size=50,
                    avg_processing_time=3.0
                )
                
                # Run adjustment loop briefly
                task = asyncio.create_task(controller.auto_adjust_loop())
                await asyncio.sleep(0.3)
                controller.stop_auto_adjust()
                await task
                
                assert mock_metrics.call_count >= 2
                assert mock_apply.call_count >= 1
    
    def test_ml_prediction_integration(self, controller):
        """Test ML-based prediction integration"""
        # Simulate historical data
        controller.scaling_history = [
            {'timestamp': datetime.now() - timedelta(minutes=5), 'cpu': 80, 'decision': 'up'},
            {'timestamp': datetime.now() - timedelta(minutes=4), 'cpu': 75, 'decision': 'up'},
            {'timestamp': datetime.now() - timedelta(minutes=3), 'cpu': 70, 'decision': 'stable'},
        ]
        
        prediction = controller.predict_optimal_workers()
        assert isinstance(prediction, int)
        assert controller.min_workers <= prediction <= controller.max_workers
    
    def test_resource_monitor_integration(self, controller):
        """Test resource monitor integration"""
        monitor = controller.resource_monitor
        
        snapshot = monitor.get_snapshot()
        assert 'cpu_percent' in snapshot
        assert 'memory_percent' in snapshot
        assert 'io_counters' in snapshot
        assert 'network_io' in snapshot
    
    def test_scaling_strategy_aggressive(self, controller):
        """Test aggressive scaling strategy"""
        controller.scaling_strategy = "aggressive"
        controller.current_workers = 5
        
        metrics = ConcurrencyMetrics(
            cpu_percent=75.0,  # Just above target
            memory_percent=70.0,
            active_workers=5,
            queue_size=50,
            avg_processing_time=2.5
        )
        
        decision = controller.should_scale_up(metrics)
        assert decision.should_scale is True
        assert decision.new_worker_count == 7  # Aggressive: +2 workers
    
    def test_scaling_strategy_conservative(self, controller):
        """Test conservative scaling strategy"""
        controller.scaling_strategy = "conservative"
        controller.current_workers = 5
        
        metrics = ConcurrencyMetrics(
            cpu_percent=85.0,  # Well above target
            memory_percent=70.0,
            active_workers=5,
            queue_size=50,
            avg_processing_time=2.5
        )
        
        decision = controller.should_scale_up(metrics)
        assert decision.should_scale is True
        assert decision.new_worker_count == 6  # Conservative: +1 worker
    
    def test_queue_size_trigger(self, controller):
        """Test queue size based scaling trigger"""
        controller.queue_threshold = 50
        
        metrics = ConcurrencyMetrics(
            cpu_percent=50.0,
            memory_percent=50.0,
            active_workers=3,
            queue_size=100,  # High queue size
            avg_processing_time=2.0
        )
        
        decision = controller.should_scale_up(metrics)
        assert decision.should_scale is True
        assert decision.reason == "High queue size"
    
    def test_processing_time_trigger(self, controller):
        """Test processing time based scaling trigger"""
        controller.target_processing_time = 2.0
        
        metrics = ConcurrencyMetrics(
            cpu_percent=60.0,
            memory_percent=60.0,
            active_workers=3,
            queue_size=30,
            avg_processing_time=5.0  # Slow processing
        )
        
        decision = controller.should_scale_up(metrics)
        assert decision.should_scale is True
        assert decision.reason == "High processing time"
    
    def test_get_scaling_history(self, controller):
        """Test scaling history retrieval"""
        # Add some history
        for i in range(3):
            decision = ScalingDecision(True, "up", i+2, f"Test {i}")
            controller.apply_scaling_decision(decision)
            time.sleep(0.1)
        
        history = controller.get_scaling_history(limit=2)
        assert len(history) == 2
        assert history[0]['new_count'] == 4  # Most recent first
    
    def test_reset_controller(self, controller):
        """Test controller reset"""
        controller.current_workers = 5
        controller.scaling_history = [1, 2, 3]
        
        controller.reset()
        
        assert controller.current_workers == controller.min_workers
        assert controller.scaling_history == []
    
    def test_export_metrics(self, controller):
        """Test metrics export for monitoring"""
        metrics = controller.export_metrics()
        
        assert 'current_workers' in metrics
        assert 'target_cpu_percent' in metrics
        assert 'scaling_history_count' in metrics
        assert 'last_scaling_timestamp' in metrics
    
    def test_concurrent_scaling_protection(self, controller):
        """Test protection against concurrent scaling operations"""

        with patch.object(controller, '_scaling_lock') as mock_lock:
            mock_lock.acquire.return_value = False  # Lock already held
            
            decision = ScalingDecision(True, "up", 5, "Test")
            result = controller.apply_scaling_decision(decision)
            
            assert result is False  # Scaling rejected due to lock