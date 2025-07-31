# create_db.py

from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import os

Base = declarative_base()

class Packet(Base):
    __tablename__ = 'packets'
    id = Column(Integer, primary_key=True)
    packet_name = Column(String(255))

def setup_database(destination_folder):
    db_path = os.path.join(destination_folder, "inspire2.db")
    engine = create_engine(f"sqlite:///{db_path}")
    Session = sessionmaker(bind=engine)
    session = Session()

    # Create the Packet table if it doesn't exist
    Base.metadata.create_all(engine)
    print(f"[SUCCESS] Database created at: {db_path}")
    return engine, Session, session
