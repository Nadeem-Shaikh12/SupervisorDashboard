import os
import sys
import time
import logging

# Add project root to path so we can import local modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from database.db import get_pending_inspections, mark_inspections_synced
from database.mongo_db import get_mongo_client, get_inspections_collection

logger = logging.getLogger("dreamvision.mongo_sync")
logging.basicConfig(level=logging.INFO)

def sync_to_atlas():
    """
    Reads unsynced records from the local Edge SQLite DB and pushes them to MongoDB Atlas.
    """
    client = get_mongo_client()
    if not client:
        return
        
    try:
        inspections_collection = get_inspections_collection(client)
        
        # 1. Fetch records that haven't been synced from local SQLite
        unsynced_records = get_pending_inspections() 
        
        if not unsynced_records:
            return

        # 2. Format them as JSON dictionaries (MongoDB Documents)
        documents = []
        for record in unsynced_records:
            doc = {
                "local_id": record["part_uid"],
                "component_name": record["component_name"],
                "timestamp": record["timestamp"],
                "status": record["status"],
                "temperature": record["temperature"],
                "image_path": record["image_path"],
                "verified_status": record.get("verified_status", "Pending")
            }
            documents.append(doc)

        # 3. Bulk insert to MongoDB
        if documents:
            result = inspections_collection.insert_many(documents)
            logger.info(f"Successfully synced {len(result.inserted_ids)} records to MongoDB Atlas.")

            # 4. Mark as synced in local SQLite so they aren't pushed again
            record_ids = [r["part_uid"] for r in unsynced_records]
            mark_inspections_synced(record_ids)

    except Exception as e:
        logger.error(f"Error during MongoDB sync: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    logger.info("Starting MongoDB Cloud Sync Daemon...")
    # Loop continuously just like the old cloud_sync daemon
    while True:
        sync_to_atlas()
        time.sleep(15)
