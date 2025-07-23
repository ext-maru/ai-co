#!/usr/bin/env python3
"""
Test immediate job execution
"""

import asyncio
import logging
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_job():
    logger.info("🎯 Async test job executed!")
    return "Success"

async def main():
    """mainメソッド"""
    scheduler = AsyncIOScheduler()
    
    # Add job to run every 10 seconds
    scheduler.add_job(test_job, 'interval', seconds=10, id='test_job', next_run_time=datetime.now())
    
    # Add job to run immediately
    scheduler.add_job(test_job, 'date', run_date=datetime.now(), id='immediate_job')
    
    scheduler.start()
    logger.info("✅ Scheduler started")
    logger.info(f"📊 Jobs: {len(scheduler.get_jobs())}")
    
    # Run for 30 seconds
    await asyncio.sleep(30)
    
    scheduler.shutdown()
    logger.info("🛑 Scheduler stopped")

if __name__ == "__main__":
    asyncio.run(main())