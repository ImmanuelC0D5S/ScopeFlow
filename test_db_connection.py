import psycopg
from backend.core.config import settings

try:
    conn = psycopg.connect(settings.database_url, connect_timeout=3)
    cur = conn.cursor()
    
    # Check tables
    cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name")
    tables = cur.fetchall()
    
    print("[OK] Connected to Neon successfully!")
    print(f"[OK] Found {len(tables)} tables:")
    for table in tables:
        print(f"  - {table[0]}")
    
    # Check if we can query projects table
    cur.execute("SELECT COUNT(*) FROM projects")
    count = cur.fetchone()[0]
    print(f"\n[OK] Projects table accessible (contains {count} rows)")
    
    conn.close()
    print("\n[OK] Database verification complete!")
    
except Exception as e:
    print(f"[ERROR] Database connection failed: {e}")
    exit(1)

# Made with Bob
