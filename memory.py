

import json
import os

MEMORY_FILE = "memory.json"


# 🔎 SEARCH MEMORY
def search_memory(query):

    if not os.path.exists(MEMORY_FILE):
        return []

    with open(MEMORY_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    results = []

    query = query.lower()

    for item in data:

        topic = item.get("topic", "").lower()

        # Partial keyword match
        if any(word in topic for word in query.split()):

            results.append(item)

    return results


# 💾 SAVE MEMORY
def save_memory(entry):

    # Load existing memory
    if os.path.exists(MEMORY_FILE):

        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

    else:

        data = []

    topic = entry.get("topic", "").lower()

    # Prevent duplicates
    for item in data:

        if topic == item.get("topic", "").lower():

            print("DEBUG duplicate memory skipped")

            return

    # Add new memory
    data.append(entry)

    # Save file
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:

        json.dump(data, f, indent=2)

    print("DEBUG memory saved")


