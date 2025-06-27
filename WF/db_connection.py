import os
import pymysql
from sqlalchemy import create_engine
from dotenv import load_dotenv

# Load environment variables from parent directory
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

def get_db_connection():
    """Create and return a PyMySQL database connection."""
    return pymysql.connect(
        host=os.getenv('SPIDERSYNC_DEV_HOST'),
        port=int(os.getenv('SPIDERSYNC_DEV_PORT')),
        user=os.getenv('SPIDERSYNC_DEV_USER'),
        password=os.getenv('SPIDERSYNC_DEV_PASSWORD'),
        database=os.getenv('SPIDERSYNC_DEV_DATABASE'),
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )

def get_db_engine():
    """Create and return a SQLAlchemy engine."""
    connection_string = (
        f"mysql+pymysql://{os.getenv('SPIDERSYNC_DEV_USER')}:"
        f"{os.getenv('SPIDERSYNC_DEV_PASSWORD')}@"
        f"{os.getenv('SPIDERSYNC_DEV_HOST')}:"
        f"{os.getenv('SPIDERSYNC_DEV_PORT')}/"
        f"{os.getenv('SPIDERSYNC_DEV_DATABASE')}"
    )
    return create_engine(connection_string, echo=False)