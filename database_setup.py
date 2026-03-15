import sqlite3
import pandas as pd
from pathlib import Path

DATABASE = "ipl.db"

# -----------------------------
# Connect Database
# -----------------------------
conn = sqlite3.connect(DATABASE)
cursor = conn.cursor()

print("Connected to database")

# -----------------------------
# SQLITE PERFORMANCE SETTINGS
# -----------------------------
print("Applying SQLite performance settings...")

conn.execute("PRAGMA journal_mode=WAL;")
conn.execute("PRAGMA synchronous=NORMAL;")
conn.execute("PRAGMA temp_store=MEMORY;")
conn.execute("PRAGMA cache_size=100000;")

# -----------------------------
# Load CSV Files
# -----------------------------
print("Loading CSV files...")

matches_path = Path("data/matches.csv")
deliveries_path = Path("data/deliveries.csv")

matches = pd.read_csv(matches_path, low_memory=False)
deliveries = pd.read_csv(deliveries_path, low_memory=False)

print("CSV files loaded successfully")

# -----------------------------
# Store Data in Database
# -----------------------------
print("Creating tables in database...")

matches.to_sql(
    "matches",
    conn,
    if_exists="replace",
    index=False,
    chunksize=5000
)

deliveries.to_sql(
    "deliveries",
    conn,
    if_exists="replace",
    index=False,
    chunksize=20000
)

print("Tables created successfully")

# -----------------------------
# Create Indexes (VERY IMPORTANT)
# -----------------------------
print("Creating indexes...")

indexes = [
    "CREATE INDEX IF NOT EXISTS idx_match_id ON deliveries(match_id)",
    "CREATE INDEX IF NOT EXISTS idx_batter ON deliveries(batter)",
    "CREATE INDEX IF NOT EXISTS idx_bowler ON deliveries(bowler)",
    "CREATE INDEX IF NOT EXISTS idx_dismissal ON deliveries(dismissal_kind)",
    "CREATE INDEX IF NOT EXISTS idx_season ON matches(season)",
    "CREATE INDEX IF NOT EXISTS idx_winner ON matches(winner)",
    "CREATE INDEX IF NOT EXISTS idx_venue ON matches(venue)"
]

for index in indexes:
    cursor.execute(index)

conn.commit()

print("Indexes created successfully")

# -----------------------------
# Database Summary
# -----------------------------
print("\nDatabase Summary")

cursor.execute("SELECT COUNT(*) FROM matches")
matches_count = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM deliveries")
deliveries_count = cursor.fetchone()[0]

print(f"Total Matches: {matches_count}")
print(f"Total Deliveries: {deliveries_count}")

print("\nDatabase setup completed successfully!")

# -----------------------------
# Close Connection
# -----------------------------
conn.close()
print("Database connection closed")