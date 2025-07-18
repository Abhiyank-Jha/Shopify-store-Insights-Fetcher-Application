from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import os
from dotenv import load_dotenv
import logging

load_dotenv()

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", "mysql+pymysql://root:admin@localhost:3306/shopify_insights")

engine = None
SessionLocal = None

try:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=300,
        echo=False
    )
    with engine.connect() as conn:
        conn.execute("SELECT 1")
    logger.info("Database connection established successfully")
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
except Exception as e:
    logger.warning(f"Database connection failed: {str(e)}")
    logger.info("Application will run without database persistence")
    engine = None
    SessionLocal = None

Base = declarative_base()


def get_db():
    if SessionLocal is None:
        class MockSession:
            def __enter__(self):
                return self
            
            def __exit__(self, exc_type, exc_val, exc_tb):
                pass
            
            def query(self, *args):
                return MockQuery()
            
            def add(self, *args):
                pass
            
            def commit(self):
                pass
            
            def rollback(self):
                pass
            
            def close(self):
                pass
        
        class MockQuery:
            def filter(self, *args):
                return self
            
            def first(self):
                return None
            
            def all(self):
                return []
            
            def delete(self):
                pass
        
        db = MockSession()
        try:
            yield db
        finally:
            db.close()
    else:
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()


def create_tables():
    if engine is not None:
        try:
            Base.metadata.create_all(bind=engine)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Error creating database tables: {str(e)}")
    else:
        logger.info("Skipping table creation - database not available")


def drop_tables():
    if engine is not None:
        try:
            Base.metadata.drop_all(bind=engine)
            logger.info("Database tables dropped successfully")
        except Exception as e:
            logger.error(f"Error dropping database tables: {str(e)}")
    else:
        logger.info("Skipping table deletion - database not available") 