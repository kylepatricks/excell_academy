# manage/process_tasks.py (Windows compatible)
#!/usr/bin/env python
"""
Windows-compatible background task processor
"""

import os
import sys
import time
import logging
from datetime import datetime, timedelta

# Setup logging for Windows
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('excel_academy_worker.log')
    ]
)

logger = logging.getLogger(__name__)

def setup_django():
    """Initialize Django environment for Windows"""
    try:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'excell_academy.settings.dev')
        import django
        django.setup()
        logger.info("✅ Django setup completed successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to setup Django: {e}")
        return False

def main():
    """Main worker loop for Windows"""
    logger.info("🚀 Starting Excel Academy Background Worker (Windows)")
    
    if not setup_django():
        input("Press Enter to exit...")
        sys.exit(1)
    
    # Import tasks after Django setup
    try:
        from finance.tasks import process_pending_payments, send_payment_reminders
    except ImportError as e:
        logger.error(f"❌ Could not import tasks: {e}")
        input("Press Enter to exit...")
        sys.exit(1)
    
    logger.info("🔄 Entering main task loop...")
    logger.info("Press Ctrl+C to stop the worker")
    
    try:
        while True:
            current_time = datetime.now()
            
            logger.info("💸 Processing payment reminders...")
            send_payment_reminders()
            
            logger.info("🔄 Processing pending payments...")
            process_pending_payments()
            
            logger.info("😴 Sleeping for 5 minutes...")
            time.sleep(300)  # Sleep for 5 minutes
            
    except KeyboardInterrupt:
        logger.info("⏹️  Worker stopped by user")
    except Exception as e:
        logger.error(f"💥 Critical error in worker: {e}")
    finally:
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()