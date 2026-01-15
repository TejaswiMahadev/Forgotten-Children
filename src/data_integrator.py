import pandas as pd
import numpy as np

class DataIntegrator:
    """
    Integrates enrollment, biometric, and demographic datasets.
    Performs temporal alignment and calculates derived metrics.
    """

    @staticmethod
    def integrate(enrollment_df, bio_df, demo_df):
        """
        Merges datasets by PIN code and District for unified analysis.
        """
        if enrollment_df.empty or bio_df.empty:
            return pd.DataFrame()

        # Aggregate Enrollment by Pincode
        # Note: In a real scenario, we'd handle time more granularly, 
        # but for the gap analysis, we aggregate historical enrollments.
        enroll_agg = enrollment_df.groupby(['pincode', 'state', 'district']).agg({
            'age_0_5': 'sum',
            'age_5_17': 'sum',
            'age_18_greater': 'sum'
        }).reset_index()

        # Aggregate Biometric Updates by Pincode
        bio_agg = bio_df.groupby(['pincode']).agg({
            'bio_age_5_17': 'sum',
            'bio_age_17_': 'sum'
        }).reset_index()

        # Aggregate Demographic Updates by Pincode
        demo_agg = demo_df.groupby(['pincode']).agg({
            'demo_age_5_17': 'sum',
            'demo_age_17_': 'sum'
        }).reset_index() if not demo_df.empty else pd.DataFrame(columns=['pincode', 'demo_age_5_17', 'demo_age_17_'])

        # Merge
        integrated = pd.merge(enroll_agg, bio_agg, on='pincode', how='left')
        integrated = pd.merge(integrated, demo_agg, on='pincode', how='left')

        # Fill NAs with 0
        fill_cols = ['bio_age_5_17', 'bio_age_17_', 'demo_age_5_17', 'demo_age_17_']
        integrated[fill_cols] = integrated[fill_cols].fillna(0).astype(int)

        return integrated
