import pandas as pd
import numpy as np

class DataCleaner:
    """
    Cleans and normalizes Aadhar datasets including date formats, 
    PIN codes, and geography names.
    """

    @staticmethod
    def clean(df, category):
        """
        Cleans the dataframe based on the category.
        """
        if df.empty:
            return df
            
        df = df.copy()

        # 1. Date Normalization (FR-1.2)
        if 'date' in df.columns:
            # Try multiple formats if needed, here we assume it might be DD-MM-YYYY or ISO
            df['date'] = pd.to_datetime(df['date'], errors='coerce')
            df = df.dropna(subset=['date'])

        # 2. PIN Code Normalization (FR-1.2)
        if 'pincode' in df.columns:
            # Ensure 6 digits, leading zeros
            df['pincode'] = df['pincode'].apply(lambda x: str(int(float(x))).zfill(6) if pd.notnull(x) else x)

        # 3. Geography Normalization (FR-1.2)
        if 'state' in df.columns:
            df['state'] = df['state'].str.strip().str.title()
        if 'district' in df.columns:
            df['district'] = df['district'].str.strip().str.title()

        # 4. Fill missing counts with 0 (DQ-1)
        count_cols = [col for col in df.columns if 'age_' in col or 'bio_' in col or 'demo_' in col]
        df[count_cols] = df[count_cols].fillna(0).astype(int)

        # 5. Remove Duplicates (FR-1.2)
        df = df.drop_duplicates()

        return df
