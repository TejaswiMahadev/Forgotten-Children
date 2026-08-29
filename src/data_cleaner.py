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
            # Coerce before formatting: a single non-numeric PIN used to raise
            # ValueError and abort the whole load. Non-integral values are data
            # errors, not something to silently truncate.
            numeric_pin = pd.to_numeric(df['pincode'], errors='coerce')
            numeric_pin = numeric_pin.where(numeric_pin % 1 == 0)

            pin_str = numeric_pin.astype('Int64').astype('string').str.zfill(6)
            # A valid Indian PIN is exactly 6 digits and never starts with 0.
            valid = pin_str.str.fullmatch(r'[1-9]\d{5}').fillna(False)

            rejected = int((~valid).sum())
            if rejected:
                print(f"DataCleaner[{category}]: dropped {rejected} rows with unusable PIN codes.")

            df['pincode'] = pin_str
            df = df[valid].copy()
            df['pincode'] = df['pincode'].astype(str)

        # 3. Geography Normalization (FR-1.2)
        if 'state' in df.columns:
            df['state'] = df['state'].str.strip().str.title()
        if 'district' in df.columns:
            df['district'] = df['district'].str.strip().str.title()

        # 4. Fill missing counts with 0 (DQ-1)
        count_cols = [col for col in df.columns if 'age_' in col or 'bio_' in col or 'demo_' in col]
        for col in count_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).round().astype(int)

        # 5. Remove Duplicates (FR-1.2)
        df = df.drop_duplicates()

        return df
