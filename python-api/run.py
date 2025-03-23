import uvicorn
import logging
from sqlalchemy.orm import Session

from app.db.init_db import init_db
from app.db.base import SessionLocal
from app.core.config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

def init() -> None:
    """Initialize the application"""
    logger.info("Initializing the database...")
    db = SessionLocal()
    try:
        init_db(db)
    finally:
        db.close()

def main() -> None:
    """Run the application"""
    logger.info("Initializing the application...")
    init()
    logger.info("Starting the API server...")
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )

if __name__ == "__main__":
    main()
