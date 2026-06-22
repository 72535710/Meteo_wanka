from sqlalchemy import create_engine, text
import urllib.parse
from sqlalchemy.orm import sessionmaker

# Settings
SERVER = r"localhost\SQLEXPRESS"
DATABASE = "MeteoWanka"
DRIVER = "ODBC Driver 18 for SQL Server"

# Build an ODBC connection string and URL-encode it. This is the most
# reliable way to pass the full ODBC connection string to SQLAlchemy + pyodbc.
odbc_params = (
    f"DRIVER={{{DRIVER}}};"
    f"SERVER={SERVER};"
    f"DATABASE={DATABASE};"
    "Trusted_Connection=yes;"
    "TrustServerCertificate=yes;"
    "Connection Timeout=5;"
)
odbc_conn_str = urllib.parse.quote_plus(odbc_params)
connection_string = f"mssql+pyodbc:///?odbc_connect={odbc_conn_str}"

# Create engine with a pre-ping and a small pool to avoid long hangs.
engine = create_engine(connection_string, pool_pre_ping=True, pool_size=5, max_overflow=10, pool_timeout=10)

def test_connection():
    """Run a minimal query to verify connectivity.

    Returns the scalar result of `SELECT 1` or raises the original exception.
    """
    with engine.connect() as conn:
        return conn.execute(text("SELECT 1")).scalar()

if __name__ == "__main__":
    try:
        print("Conexión creada correctamente, prueba:", test_connection())
    except Exception as e:
        print("Error al conectar:", e)
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)        