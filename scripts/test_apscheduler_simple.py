#!/usr/bin/env python3
"""
Simple APScheduler test
"""

import time
import logging
from apscheduler.schedulers.background import BackgroundScheduler

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

def test_job():
    logger.info("🎯 Test job executed!")

if __name__ == "__main__":
    scheduler = BackgroundScheduler()
    
    # Add job to run every 10 seconds
    scheduler.add_job(test_job, 'interval', seconds=10, id='test_job')
    
    scheduler.start()
    logger.info("✅ Scheduler started - job will run every 10 seconds")
    
    try:
        # Keep running for 30 seconds
        time.sleep(30)
    except KeyboardInterrupt:
        pass
    
    scheduler.shutdown()
    logger.info("🛑 Scheduler stopped")