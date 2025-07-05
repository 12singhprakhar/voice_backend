from database import SessionLocal, Entry

db = SessionLocal()

# Delete all rows
db.query(Entry).delete()

# Commit changes
db.commit()

print("✅ All entries deleted.")

db.close()
