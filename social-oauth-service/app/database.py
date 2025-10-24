"""
Database connection and session management
"""
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from typing import Generator
import logging

from app.config import settings

logger = logging.getLogger(__name__)


class Database:
    """Database connection manager"""
    
    def __init__(self):
        self.connection_params = {
            'host': settings.DB_HOST,
            'port': settings.DB_PORT,
            'database': settings.DB_NAME,
            'user': settings.DB_USER,
            'password': settings.DB_PASSWORD
        }
    
    @contextmanager
    def get_connection(self) -> Generator:
        """Get database connection with automatic cleanup"""
        conn = None
        try:
            conn = psycopg2.connect(**self.connection_params)
            yield conn
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    @contextmanager
    def get_cursor(self, cursor_factory=RealDictCursor) -> Generator:
        """Get database cursor with automatic connection management"""
        with self.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=cursor_factory)
            try:
                yield cursor
            finally:
                cursor.close()
    
    def execute_query(self, query: str, params: tuple = None, fetch: bool = True):
        """Execute a query and optionally fetch results"""
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            if fetch:
                return cursor.fetchall()
            return None
    
    def execute_insert(self, query: str, params: tuple = None, returning: bool = True):
        """Execute an insert query and return the inserted row"""
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            if returning:
                return cursor.fetchone()
            return None
    
    def execute_update(self, query: str, params: tuple = None, returning: bool = False):
        """Execute an update query"""
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            if returning:
                return cursor.fetchone()
            return cursor.rowcount
    
    def execute_delete(self, query: str, params: tuple = None):
        """Execute a delete query"""
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            return cursor.rowcount
    
    def test_connection(self) -> bool:
        """Test database connection"""
        try:
            with self.get_cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                return result is not None
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False
    
    def initialize_schema(self, schema_file: str = None):
        """Initialize database schema from SQL file"""
        if not schema_file:
            schema_file = "migrations/init_oauth_schema.sql"
        
        try:
            with open(schema_file, 'r') as f:
                schema_sql = f.read()
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(schema_sql)
                cursor.close()
            
            logger.info("Database schema initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize database schema: {e}")
            raise


# Global database instance
db = Database()
