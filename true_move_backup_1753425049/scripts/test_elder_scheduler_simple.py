#!/usr/bin/env python3
"""
Simple Elder Scheduler Test
"""

import asyncio
import logging
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from libs.apscheduler_integration import get_elder_scheduler, ElderScheduleDecorators

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize scheduler
scheduler = get_elder_scheduler()
decorators = ElderScheduleDecorators(scheduler)

# Define test task
@decorators.scheduled('interval', seconds=10)
async def test_auto_issue():
    """Test task that runs every 10 seconds"""
    logger.info("🤖 Test Auto Issue Processor running!")
    logger.info(f"   Current time: {datetime.now()}")
    # Simulate async work
    await asyncio.sleep(1)
    logger.info("✅ Test task completed!")
    
# Start scheduler
scheduler.start()
logger.info("🚀 Test scheduler started")
logger.info(f"📊 Jobs: {len(scheduler.scheduler.get_jobs())}")

# Run event loop
try:
    logger.info("⚡ Running AsyncIO event loop...")
    asyncio.get_event_loop().run_forever()
except KeyboardInterrupt:
    logger.info("🛑 Shutting down...")
    scheduler.shutdown()