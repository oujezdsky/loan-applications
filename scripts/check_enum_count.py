import sys
sys.path.append("/app")
from app.sync_database import SessionLocal
from app.models.enums import EnumType

db = SessionLocal()
count = db.query(EnumType).count()
db.close()

print(count)
