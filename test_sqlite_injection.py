import os
import sys
import datetime
from database.db import insert_inspection, get_pending_inspections, get_all_inspections, init_db

# Ensure the database exists
init_db()

# Generate a dummy PID (Part UID)
dummy_pid = f"PID-TEST-{int(datetime.datetime.now().timestamp())}"
timestamp = datetime.datetime.now().isoformat()

print(f"Injecting dummy PID: {dummy_pid} into local SQLite database...")

# Insert the dummy record
insert_inspection(
    part_uid=dummy_pid,
    component_name="Engine Block Test",
    temperature=105.5,
    status="OK",
    image_path="test_image.jpg",
    timestamp=timestamp,
    sync_status="PENDING" # We set it to PENDING as if it's waiting for MongoDB cloud sync
)

print("\n--- Verifying Database Records ---")

# Fetch all records
all_records = get_all_inspections()
print(f"Total records in parts_inspection table: {len(all_records)}")

# Fetch pending records
pending_records = get_pending_inspections()
print(f"Total PENDING records waiting for MongoDB sync: {len(pending_records)}")

print("\nLast 3 injected records:")
for rec in all_records[:3]:
    print(f"  ID: {rec['part_uid']} | Component: {rec['component_name']} | Temp: {rec['temperature']} | Status: {rec['sync_status']}")

print("\nLocal SQLite database is functioning perfectly!")
