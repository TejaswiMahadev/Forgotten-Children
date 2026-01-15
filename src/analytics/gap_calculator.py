import pandas as pd
import numpy as np

class GapCalculator:
    """
    Calculates expected vs actual biometric updates to identify gaps.
    """
    
    @staticmethod
    def calculate_gaps(integrated_df):
        """
        Computes absolute and percentage gaps.
        Since historical enrollments (5-10 years ago) are missing in the 
        current dataset, we use a cohort multiplier heuristic.
        
        Heuristic:
        Expected Updates (5-17) = Current Enrollment (0-5) * CohortFactor (12.0)
        Actual = BioUpdates(5-17)
        """
        if integrated_df.empty:
            return integrated_df

        df = integrated_df.copy()
        
        # FR-2.1: Expected Update Calculation (Heuristic for Hackathon)
        # 0-5 enrollment (5 year span) vs 5-17 updates (12 year span)
        # A factor of 12.0 represents a stable population plus 
        # the PRD's "forgotten" cohort multiplier.
        df['total_expected'] = (df['age_0_5'] * 12.0).astype(int)
        
        # Ensure we have at least a baseline for expected updates
        df.loc[df['total_expected'] < df['bio_age_5_17'], 'total_expected'] = (df['bio_age_5_17'] * 1.2).astype(int)
        
        # FR-2.2: Actual Update Measurement
        df['actual_bio_updates'] = df['bio_age_5_17']
        
        # Compute Gaps
        df['update_gap'] = df['total_expected'] - df['actual_bio_updates']
        # Handle cases where expected is 0 to avoid division by zero
        df['update_rate'] = (df['actual_bio_updates'] / df['total_expected'].replace(0, np.nan)) * 100
        df['update_rate'] = df['update_rate'].fillna(0).clip(0, 100)
        
        df['gap_percentage'] = 100 - df['update_rate']
        
        # FR-2.3: Risk Categorization
        def assign_risk(gap_pct):
            if gap_pct >= 70: return 'Critical'
            if gap_pct >= 50: return 'High'
            if gap_pct >= 30: return 'Medium'
            return 'Low'
            
        df['risk_level'] = df['gap_percentage'].apply(assign_risk)
        
        return df

    @staticmethod
    def calculate_detailed_metrics(df):
        """
        FR-2.4: Detailed Awareness & Data Health metrics.
        - Saturation Index: How well biometrics keep up with demographic updates.
        - Enrollment Buffer: Untapped population (0-5) vs potential capacity.
        """
        if df.empty:
            return df
            
        # Saturation: High means people updating demographics are ALSO updating biometrics
        # Normalized to 0-100%
        df['saturation_index'] = (df['bio_age_5_17'] / df['demo_age_5_17'].replace(0, 1) * 100).clip(0, 100)
        
        # State Average Comparison
        state_avg = df.groupby('state')['update_rate'].transform('mean')
        df['vs_state_avg'] = df['update_rate'] - state_avg
        
        return df

    @staticmethod
    def get_summary_stats(gap_df):
        """
        Returns high-level KPI metrics for the dashboard.
        """
        if gap_df.empty:
            return {}
            
        stats = {
            'total_at_risk': int(gap_df['update_gap'].sum()),
            'critical_pins': int((gap_df['risk_level'] == 'Critical').sum()),
            'overall_update_rate': float(gap_df['actual_bio_updates'].sum() / gap_df['total_expected'].sum() * 100) if gap_df['total_expected'].sum() > 0 else 0,
            'high_risk_pins': int((gap_df['risk_level'] == 'High').sum())
        }
        return stats
