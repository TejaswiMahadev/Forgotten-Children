import pandas as pd
import numpy as np

class AnomalyDetector:
    """
    Detects behavioral and statistical anomalies in Aadhar update data.
    """
    
    @staticmethod
    def detect_anomalies(integrated_df):
        """
        FR-6.1 & FR-6.2: Anomaly Detection
        Identifies bio-demo mismatches and statistical outliers.
        """
        if integrated_df.empty:
            return pd.DataFrame()
            
        df = integrated_df.copy()
        anomalies = []

        # 1. Bio-Demo Mismatch (High demo, Low bio)
        # Type: People updating addresses but not biometrics
        mask_mismatch = (df['demo_age_5_17'] > (df['bio_age_5_17'] * 2)) & (df['demo_age_5_17'] > 50)
        mismatch_df = df[mask_mismatch].copy()
        mismatch_df['anomaly_type'] = 'Bio-Demo Mismatch'
        mismatch_df['severity'] = 'High'
        mismatch_df['description'] = 'Demographic updates significantly outpace biometric updates.'
        anomalies.append(mismatch_df)

        # 2. Statistical Outliers in update rate (Low outliers)
        q1 = df['update_rate'].quantile(0.25)
        q3 = df['update_rate'].quantile(0.75)
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        
        mask_outlier = (df['update_rate'] < lower_bound)
        outlier_df = df[mask_outlier].copy()
        outlier_df['anomaly_type'] = 'Statistical Outlier'
        outlier_df['severity'] = 'Critical'
        outlier_df['description'] = 'Update rate is statistically lower than peers.'
        anomalies.append(outlier_df)

        # 3. High Migration Indicator (Updates > Enrollment)
        mask_migration = (df['bio_age_5_17'] > df['age_0_5']) & (df['age_0_5'] > 0)
        migration_df = df[mask_migration].copy()
        migration_df['anomaly_type'] = 'Potential High In-Migration'
        migration_df['severity'] = 'Medium'
        migration_df['description'] = 'Biometric updates exceed original enrollment counts.'
        anomalies.append(migration_df)

        if not anomalies:
            return pd.DataFrame()
            
        return pd.concat(anomalies, ignore_index=True)
