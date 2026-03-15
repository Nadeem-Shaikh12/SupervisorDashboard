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
from database.mongo_db import get_mongo_client, get_inspections_collection

logger = logging.getLogger("dreamvision.cloud")

class CloudSynchronizer:
    def __init__(self, interval_seconds=15):
        self.interval = interval_seconds
        self.running = False
        self._thread = None

    def start(self):
        """Starts the background sync thread."""
        if not self.running:
            self.running = True
            self._thread = threading.Thread(target=self._sync_loop, daemon=True, name="cloud-sync")
            self._thread.start()
            logger.info("MongoDB Cloud synchronization background worker started.")

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
        """Fetches pending data from SQLite and pushes to MongoDB Atlas."""
        client = get_mongo_client()
        if not client:
            return

        try:
            pending = get_pending_inspections()
            if not pending:
                return

            collection = get_inspections_collection(client)
            if collection is None:
                return

            documents = []
            for record in pending:
                doc = {
                    "part_uid": record["part_uid"],
                    "component_name": record["component_name"],
                    "temperature": record["temperature"],
                    "status": record["status"],
                    "device_id": record.get("device_id", "Unknown"),
                    "image_path": record["image_path"],
                    "timestamp": record["timestamp"],
                    "verified_status": record.get("verified_status", "Pending")
                }
                documents.append(doc)

            if documents:
                result = collection.insert_many(documents)
                logger.info(f"Successfully synced {len(result.inserted_ids)} records to MongoDB Atlas.")
                
                # Update SQLite sync_status to SYNCED
                mark_inspections_synced([doc["part_uid"] for doc in documents])

        except Exception as e:
            logger.error(f"Error during MongoDB sync: {e}")
        finally:
            client.close()
