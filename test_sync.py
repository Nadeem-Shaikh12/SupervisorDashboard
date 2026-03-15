import os
import sys
import logging
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from edge_server.cloud.cloud_sync import CloudSynchronizer
from database.db import init_db

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    load_dotenv()
    init_db()
    
    sync = CloudSynchronizer()
    print("Forcing sync now...")
    sync.sync_now()
    print("Sync check complete.")
