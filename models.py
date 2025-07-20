from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Packet(Base):
    __tablename__ = 'packets'

    id = Column(Integer, primary_key=True)
    packet_name = Column(String, unique=True)   
