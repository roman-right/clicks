from pymongo import MongoClient
import random
import time

# Connect to MongoDB
client = MongoClient('mongodb://articles:articles@localhost:27017/')
db = client["clicksDB"]

# Create or reset the clicks collection
clicks = db["clicks"]
clicks.drop()

print("Generating random clicks data...")
to_insert = []
width = 1920
height = 1080

for _ in range(1, 10_000_000):
    # Let's make hot zones in the corners
    if random.random() < 0.3:
        x = random.randint(0, 100)
        y = random.randint(0, 100)
    elif random.random() < 0.3:
        x = random.randint(width - 100, width)
        y = random.randint(height - 100, height)
    elif random.random() < 0.3:
        x = random.randint(width - 100, width)
        y = random.randint(0, 100)
    else:
        x = random.randint(0, width)
        y = random.randint(0, height)

    timestamp = random.randint(1_000_000_000, 1_600_000_000)
    to_insert.append({"x": x, "y": y, "timestamp": timestamp})
    if _ % 100_000 == 0:
        result = clicks.insert_many(to_insert)
        to_insert = []
        print(f"Inserted {_} clicks")
clicks.insert_many(to_insert)

# Unoptimized pipeline
unoptimized_pipeline = [
    {
        "$project": {
            "binX": {"$floor": {"$divide": ["$x", 100]}},
            "binY": {"$floor": {"$divide": ["$y", 100]}}
        }
    },
    {
        "$group": {
            "_id": {"binX": "$binX", "binY": "$binY"},
            "count": {"$sum": 1}
        }
    },
    {"$sort": {"count": -1}},
    {"$limit": 3}
]

# Optimized pipeline
optimized_pipeline = [
    {"$sample": {"size": 100000}},
    {
        "$project": {
            "binX": {"$floor": {"$divide": ["$x", 100]}},
            "binY": {"$floor": {"$divide": ["$y", 100]}}
        }
    },
    {
        "$group": {
            "_id": {"binX": "$binX", "binY": "$binY"},
            "sampledCount": {"$sum": 1}
        }
    },
    {"$sort": {"sampledCount": -1}},
    {"$limit": 3}
]

# Measure time taken by unoptimized pipeline
start_time = time.time()
result_unoptimized = list(clicks.aggregate(unoptimized_pipeline))
end_time = time.time()
print(f"Unoptimized pipeline took {end_time - start_time:.2f} seconds.")

# Measure time taken by optimized pipeline
start_time = time.time()
result_optimized = list(clicks.aggregate(optimized_pipeline))
end_time = time.time()
print(f"Optimized pipeline took {end_time - start_time:.2f} seconds.")

print(f"Unoptimized result: {result_unoptimized}")
print(f"Optimized result: {result_optimized}")

client.close()
