import sqlite3

conn = sqlite3.connect('instance/placement.db')
cursor = conn.cursor()

# Get all CREATE TABLE statements
schema = cursor.execute("SELECT sql FROM sqlite_master WHERE type='table';").fetchall()

for table in schema:
    print(table[0] + ";\n")