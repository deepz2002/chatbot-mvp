"""
SQLite Fix for Streamlit Cloud
This MUST be imported before any ChromaDB imports
"""
import sys

def fix_sqlite():
    """Fix SQLite version compatibility for Streamlit Cloud"""
    try:
        # Force pysqlite3 to replace sqlite3 for ChromaDB compatibility
        __import__('pysqlite3')
        sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
        print("✅ SQLite fix applied successfully")
        return True
    except ImportError:
        print("⚠️ pysqlite3 not available, using system sqlite3")
        return False

# Apply the fix immediately when this module is imported
fix_sqlite()
