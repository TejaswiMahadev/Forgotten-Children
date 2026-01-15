from data_loader import UIDAIDataLoader
import os
import pandas as pd

def clean_and_save_datasets(base_path):
    loader = UIDAIDataLoader(base_path)
    processed_path = os.path.join(base_path, 'processed_data')
    os.makedirs(processed_path, exist_ok=True)
    
    categories = ['enrollment', 'demographic', 'biometric']
    
    for cat in categories:
        print(f"Processing category: {cat}...")
        df = loader.load_dataset(cat)
        if not df.empty:
            # Align temporal granularity: daily -> monthly if required
            # For these datasets, we might want to keep daily but provide a monthly view
            df['month'] = df['date'].dt.to_period('M').astype(str)
            
            output_file = os.path.join(processed_path, f"{cat}_combined.csv")
            df.to_csv(output_file, index=False)
            print(f"Saved {cat} to {output_file}")
            print(loader.validate_dataset(df, cat))
        else:
            print(f"No data found for {cat}")

if __name__ == "__main__":
    base_path = r'c:\Users\mahad\OneDrive\Desktop\UIDAI'
    clean_and_save_datasets(base_path)
