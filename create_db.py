from sqlalchemy import create_engine, Column, Integer
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import String
import os

engine = create_engine('sqlite:///inspire2.db')

Session = sessionmaker(bind=engine)
session = Session()

Base = declarative_base()

class Packet(Base):
    __tablename__ = 'packets'
    id = Column(Integer, primary_key=True)
    packet_name = Column(String(255))
Base.metadata.create_all(engine)

print("[SUCCESS] Database and Packet table created!")

if __name__ == "__main__":
    new_packet = Packet(packet_name="Demo Packet")
    session.add(new_packet)
    session.commit()
    print("New packet added to the database.")

    packet = session.query(Packet).filter_by(packet_name="Demo Packet").first()
    print(f"Retrieved packet: {packet.packet_name} with ID: {packet.id}")