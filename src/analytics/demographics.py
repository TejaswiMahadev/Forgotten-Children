import pandas as pd
import numpy as np

class DemographicAnalytics:
    def __init__(self, df):
        self.df = df
        # Pre-compute common derived columns
        update_cols = ['demo_age_5_17', 'demo_age_17_']
        if all(col in self.df.columns for col in update_cols):
            self.df['total_updates'] = self.df[update_cols].sum(axis=1)

    def get_age_behavior(self):
        """Analyzes update types by age group."""
        groups = self.df.groupby('month')[['demo_age_5_17', 'demo_age_17_']].sum().reset_index()
        return groups

    def get_life_event_signals(self):
        """
        Identifies potential marriage-linked changes or documentation maturity issues.
        Signals: Update frequency shifts.
        """
        # We look for districts with high demo_age_17_ updates relative to total
        district_stats = self.df.groupby('district')[['demo_age_5_17', 'demo_age_17_']].sum()
        district_stats['total'] = district_stats.sum(axis=1)
        district_stats['adult_update_ratio'] = district_stats['demo_age_17_'] / district_stats['total']
        
        return district_stats.sort_values('adult_update_ratio', ascending=False)
    
    def get_temporal_clusters(self):
        """
        Identifies update patterns over time using temporal clustering.
        Task 3: Temporal clustering analysis.
        """
        # Ensure month column exists
        if 'month' not in self.df.columns:
            if 'date' in self.df.columns:
                self.df['date'] = pd.to_datetime(self.df['date'])
                self.df['month'] = self.df['date'].dt.to_period('M').astype(str)
        
        # Group by month and district
        temporal = self.df.groupby(['month', 'district'])[['demo_age_5_17', 'demo_age_17_']].sum().reset_index()
        temporal['total_updates'] = temporal['demo_age_5_17'] + temporal['demo_age_17_']
        
        # Calculate rolling average to identify clusters
        temporal = temporal.sort_values(['district', 'month'])
        temporal['rolling_avg'] = temporal.groupby('district')['total_updates'].transform(
            lambda x: x.rolling(window=3, min_periods=1).mean()
        )
        
        # Identify high-activity periods (clusters)
        temporal['is_cluster'] = temporal['total_updates'] > temporal['rolling_avg'] * 1.5
        
        return temporal
    
    def get_life_stage_transitions(self):
        """
        Detects marriage, relocation, and documentation events.
        Task 3: Life-stage transition indicators.
        
        Returns:
            DataFrame with transition indicators:
            - High adult updates: Potential marriage/relocation
            - Balanced updates: General documentation
            - Low updates: Stable population
        """
        district_stats = self.df.groupby('district')[['demo_age_5_17', 'demo_age_17_']].sum()
        district_stats['total'] = district_stats.sum(axis=1)
        
        # Calculate ratios
        district_stats['adult_ratio'] = district_stats['demo_age_17_'] / (district_stats['total'] + 1)
        district_stats['youth_ratio'] = district_stats['demo_age_5_17'] / (district_stats['total'] + 1)
        
        # Classify transitions
        def classify_transition(row):
            if row['adult_ratio'] > 0.7:
                return 'Marriage/Relocation Signal'
            elif row['adult_ratio'] > 0.4 and row['youth_ratio'] > 0.3:
                return 'General Documentation'
            elif row['total'] < district_stats['total'].quantile(0.25):
                return 'Stable Population'
            else:
                return 'Mixed Activity'
        
        district_stats['transition_type'] = district_stats.apply(classify_transition, axis=1)
        
        return district_stats.sort_values('adult_ratio', ascending=False)
    
    def get_documentation_maturity_score(self):
        """
        Scores districts based on update frequency patterns.
        Task 3: Documentation maturity signals.
        
        Higher scores indicate mature documentation practices.
        Lower scores indicate potential documentation gaps.
        """
        # Ensure month column exists
        if 'month' not in self.df.columns:
            if 'date' in self.df.columns:
                self.df['date'] = pd.to_datetime(self.df['date'])
                self.df['month'] = self.df['date'].dt.to_period('M').astype(str)
        
        # Calculate update consistency (lower CV = higher maturity)
        district_monthly = self.df.groupby(['district', 'month'])[['demo_age_5_17', 'demo_age_17_']].sum()
        district_monthly['total_updates'] = district_monthly.sum(axis=1)
        
        # Coefficient of variation (inverse for maturity)
        cv_by_district = district_monthly.groupby('district')['total_updates'].apply(
            lambda x: x.std() / (x.mean() + 1)
        )
        
        # Normalize to 0-100 scale (lower CV = higher maturity)
        max_cv = cv_by_district.max()
        maturity_scores = (1 - cv_by_district / (max_cv + 1e-6)) * 100
        
        result = pd.DataFrame({
            'district': maturity_scores.index,
            'maturity_score': maturity_scores.values,
            'maturity_level': pd.cut(maturity_scores.values, bins=[0, 33, 66, 100], labels=['Low', 'Medium', 'High'])
        }).sort_values('maturity_score', ascending=False)
        
        return result
    
    def get_digital_instability_patterns(self):
        """
        Identifies high-churn districts with unstable update patterns.
        Task 3: Digital instability patterns.
        """
        # Ensure month column exists
        if 'month' not in self.df.columns:
            if 'date' in self.df.columns:
                self.df['date'] = pd.to_datetime(self.df['date'])
                self.df['month'] = self.df['date'].dt.to_period('M').astype(str)
        
        # Calculate volatility
        district_monthly = self.df.groupby(['district', 'month'])[['demo_age_5_17', 'demo_age_17_']].sum()
        district_monthly['total_updates'] = district_monthly.sum(axis=1)
        
        # Calculate standard deviation and mean
        instability = district_monthly.groupby('district')['total_updates'].agg(['mean', 'std'])
        instability['instability_index'] = instability['std'] / (instability['mean'] + 1)
        
        # Flag high instability
        instability['high_instability'] = instability['instability_index'] > instability['instability_index'].quantile(0.75)
        
        return instability.sort_values('instability_index', ascending=False)

if __name__ == "__main__":
    # Test with combined demographic data
    import os
    base_path = r'c:\Users\mahad\OneDrive\Desktop\UIDAI'
    df = pd.read_csv(os.path.join(base_path, 'processed_data', 'demographic_combined.csv'))
    analytics = DemographicAnalytics(df)
    print("Demographic Behavior Sample:")
    print(analytics.get_life_event_signals().head())
