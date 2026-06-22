from database import engine
from sqlalchemy import text

try:
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1")).scalar()
        print("✅ Conexión exitosa con SQL Server, prueba:", result)
except Exception as e:
    print("❌ Error:", e)