import os
import pandas as pd
from models import Packet
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Setup SQLAlchemy engine and session
engine = create_engine('sqlite:///inspire2.db')
Session = sessionmaker(bind=engine)
session = Session()

def has_headers(file_path):
    try:
        sample = pd.read_csv(file_path, nrows=1)
        return not all(str(col).isdigit() for col in sample.columns)
    except Exception as e:
        print(f"Failed to read file {file_path}: {e}")
        return False

def process_packets(folder_path):
    foldername = os.path.basename(folder_path)
    print(f"\nProcessing folder: {foldername}")

    for level in ["Level 0 Packets", "Level 1 Packets"]:
        level_path = os.path.join(folder_path, level)
        if not os.path.exists(level_path):
            print(f"Skipping missing subfolder: {level_path}")
            continue

        for file in os.listdir(level_path):
            if file.endswith('.csv'):
                file_path = os.path.join(level_path, file)
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

                # Add packet entry if not already added
                packet = session.query(Packet).filter_by(packet_name=file).first()
                if not packet:
                    packet = Packet(packet_name=file)
                    session.add(packet)
                    session.commit()
                    print(f"Added packet to database: {file}")
                else:
                    print(f"Packet already exists: {file}")

                # Save to table with folder name prefix
                table_name = f"{foldername}_{file.replace('.csv', '')}".replace(" ", "_")
                df.to_sql(name=table_name, con=engine, if_exists='replace', index=False)
                print(f"DataFrame written to table: {table_name}")

def process_folders(main_folder_path):
    print(f"\nScanning main folder: {main_folder_path}")
    for foldername in os.listdir(main_folder_path):
        full_path = os.path.join(main_folder_path, foldername)
        if os.path.isdir(full_path) and foldername.startswith("Decoded_Packets"):
            print(f"\nFound decoded packet folder: {foldername}")
            process_packets(full_path)
    print("\nAll folders processed.")

if __name__ == "__main__":
    # CHANGE THIS to your actual main folder path
    MAIN_FOLDER_PATH = r"C:\Users\LENOVO\OneDrive\Desktop\IS1 On-orbit Data\Processed data"
    process_folders(MAIN_FOLDER_PATH)
