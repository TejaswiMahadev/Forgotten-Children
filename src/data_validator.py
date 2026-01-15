import pandas as pd
import numpy as np

class DataValidator:
    """
    Validates Aadhar datasets for schema consistency, data types, and quality.
    """
    
    SCHEMAS = {
        'enrollment': ['date', 'state', 'district', 'pincode', 'age_0_5', 'age_5_17', 'age_18_greater'],
        'biometric': ['date', 'state', 'district', 'pincode', 'bio_age_5_17', 'bio_age_17_'],
        'demographic': ['date', 'state', 'district', 'pincode', 'demo_age_5_17', 'demo_age_17_']
    }

    @staticmethod
    def validate(df, category):
        """
        Performs comprehensive validation on the dataframe.
        """
        report = {
            'category': category,
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'metrics': {
                'total_rows': len(df),
                'missing_pincode': 0,
                'negative_counts': 0
            }
        }

        if category not in DataValidator.SCHEMAS:
            report['is_valid'] = False
            report['errors'].append(f"Unknown category: {category}")
            return report

        # 1. Schema Check
        expected_cols = DataValidator.SCHEMAS[category]
        missing_cols = [col for col in expected_cols if col not in df.columns]
        if missing_cols:
            report['is_valid'] = False
            report['errors'].append(f"Missing columns: {missing_cols}")

        # 2. Null Pincode Check (FR-1.2, DQ-1)
        if 'pincode' in df.columns:
            null_pins = df['pincode'].isnull().sum()
            report['metrics']['missing_pincode'] = null_pins
            if null_pins > 0:
                report['is_valid'] = False
                report['errors'].append(f"Found {null_pins} records with missing PIN code.")

        # 3. Negative Counts (DQ-3)
        count_cols = [col for col in df.columns if 'age_' in col or 'bio_' in col or 'demo_' in col]
        for col in count_cols:
            neg_count = (df[col] < 0).sum()
            if neg_count > 0:
                report['metrics']['negative_counts'] += neg_count
                report['warnings'].append(f"Found {neg_count} negative counts in column '{col}'.")

        # 4. Date range check (DQ-3)
        if 'date' in df.columns:
            try:
                temp_date = pd.to_datetime(df['date'], errors='coerce')
                min_date, max_date = temp_date.min(), temp_date.max()
                if min_date < pd.Timestamp('2009-01-01') or max_date > pd.Timestamp('2026-12-31'):
                    report['warnings'].append(f"Date range {min_date} to {max_date} seems outside expected limits.")
            except:
                pass

        return report
