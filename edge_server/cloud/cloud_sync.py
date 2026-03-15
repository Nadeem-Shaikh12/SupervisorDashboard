"""
edge_server/cloud/cloud_sync.py
================================
Simulates periodic cloud connection fetching 'PENDING' data from SQLite 
and simulating REST pushes with retry logic to an external provider 
(e.g., AWS S3, Firebase).
"""

import time
import json
import logging
import threading
import requests

from database.db import get_pending_inspections, mark_inspections_synced

logger = logging.getLogger("dreamvision.cloud")

# Simulated cloud endpoint
CLOUD_API_URL = "https://mock-cloud.dreamvision.com/api/v1/sync/"

class CloudSynchronizer:
    def __init__(self, interval_seconds=10):
        self.interval = interval_seconds
        self.running = False
        self._thread = None

    def start(self):
        """Starts the background sync thread."""
        if not self.running:
            self.running = True
            self._thread = threading.Thread(target=self._sync_loop, daemon=True, name="cloud-sync")
            self._thread.start()
            logger.info("Cloud synchronization background worker started.")

    def stop(self):
        """Stops the synchronization worker gracefully."""
        self.running = False
        if self._thread:
            self._thread.join(timeout=5)

    def _sync_loop(self):
        while self.running:
            self.sync_now()
            time.sleep(self.interval)

    def sync_now(self):
        """Fetches pending data, simulates an upload, and acknowledges the SQLite cache."""
        pending = get_pending_inspections()
        if not pending:
            return  # Nothing to sync

        logger.info(f"Preparing to sync {len(pending)} inspection records to cloud...")

        synced_ids = []
        for record in pending:
            payload = {
                "part_uid": record["part_uid"],
                "component_name": record["component_name"],
                "temperature": record["temperature"],
                "status": record["status"],
                "timestamp": record["timestamp"],
                "image_path": record["image_path"],
                "device_id": record["device_id"] if "device_id" in record else "unknown"
            }

            try:
                # Simulated delay/error chance (in a real system we'd use requests.post)
                # resp = requests.post(CLOUD_API_URL, json=payload, timeout=5)
                # if resp.status_code == 200: ...
                
                # We simulate a successful network POST operation:
                time.sleep(0.1) 
                
                synced_ids.append(record["part_uid"])
            except requests.exceptions.RequestException as e:
                logger.error(f"Network error syncing {record['part_uid']} - will retry later. Err: {e}")
                
        if synced_ids:
            mark_inspections_synced(synced_ids)
            logger.info(f"CloudSync Success: {len(synced_ids)} records flushed directly to cloud.")
