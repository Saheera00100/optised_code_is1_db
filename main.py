import os
import pandas as pd
from models import Packet
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Setup SQLAlchemy engine and session
engine = create_engine('sqlite:///inspire2.db')
Session = sessionmaker(bind=engine)
session = Session()

FOLDER_PATH = r"c:\Users\LENOVO\OneDrive\Desktop\Decoded_Packets_2023-08-04T080757"

def has_headers(file_path):
    try:
        sample = pd.read_csv(file_path, nrows=1)
        return not all(str(col).isdigit() for col in sample.columns)
    except Exception as e:
        print(f"Failed to read file {file_path}: {e}")
        return False

def process_packets(folder_path):
    for foldername, subfolders, files in os.walk(folder_path):
        print(f"\nScanning folder: {foldername}")
        for file in files:
            if file.endswith('.csv'):
                file_path = os.path.join(foldername, file)
                print(f"\nFound file: {file}")

                header_exists = has_headers(file_path)

                try:
                    if header_exists:
                        df = pd.read_csv(file_path)
                    else:
                        df = pd.read_csv(file_path, header=None)
                        df.columns = [f'val_{i}' for i in range(df.shape[1])]
                except Exception as e:
                    print(f"Error reading {file}: {e}")
                    continue

                # Add packet entry to packets table
                packet = session.query(Packet).filter_by(packet_name=file).first()
                if not packet:
                    packet = Packet(packet_name=file)
                    session.add(packet)
                    session.commit()
                    print(f"Added packet to database: {file}")
                else:
                    print(f"Packet already exists: {file}")

                # You can now process the DataFrame 'df' as needed
                print(f"DataFrame for {file}:")
                print(df.head())
                df.to_sql(name=file.replace('.csv', ''), con=engine, if_exists='replace', index=False)
                print(f"DataFrame written to table: {file.replace('.csv', '')}")

    print("\nProcessing complete.")

if __name__ == "__main__":
    process_packets(FOLDER_PATH)
