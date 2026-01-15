import pandas as pd
import numpy as np

class BiometricAnalytics:
    def __init__(self, df):
        self.df = df
        # Pre-compute common derived columns
        bio_cols = ['bio_age_5_17', 'bio_age_17_']
        if all(col in self.df.columns for col in bio_cols):
            self.df['total_bio_updates'] = self.df[bio_cols].sum(axis=1)

    def get_biometric_stress_index(self):
        """
        Computes the Biometric Stress Index per district.
        Based on high update rates in the 17+ age group (often manual labor related).
        """
        district_stats = self.df.groupby('district')[['bio_age_5_17', 'bio_age_17_']].sum()
        district_stats['total_bio_updates'] = district_stats.sum(axis=1)
        
        # Biometric Stress Index (Z-score of updates in 17+)
        mean_v = district_stats['bio_age_17_'].mean()
        std_v = district_stats['bio_age_17_'].std()
        district_stats['biometric_stress_index'] = (district_stats['bio_age_17_'] - mean_v) / std_v
        
        return district_stats.sort_values('biometric_stress_index', ascending=False)

    def get_modality_dominance(self):
        """
        In a real scenario, we'd have modality types (fingerprint, iris).
        Here we distinguish by age-wise churn.
        """
        # Ratio of adult updates to child updates
        self.df['churn_ratio'] = self.df['bio_age_17_'] / (self.df['bio_age_5_17'] + 1)
        return self.df.groupby('district')['churn_ratio'].mean().sort_values(ascending=False)
    
    def get_modality_timeseries(self):
        """
        Tracks biometric updates over time by age group.
        Task 4: Modality-wise time-series tracking.
        """
        # Ensure month column exists
        if 'month' not in self.df.columns:
            if 'date' in self.df.columns:
                self.df['date'] = pd.to_datetime(self.df['date'])
                self.df['month'] = self.df['date'].dt.to_period('M').astype(str)
        
        # Group by month
        timeseries = self.df.groupby('month')[['bio_age_5_17', 'bio_age_17_']].sum().reset_index()
        timeseries['total_bio_updates'] = timeseries['bio_age_5_17'] + timeseries['bio_age_17_']
        
        # Calculate rolling averages
        timeseries['rolling_3m'] = timeseries['total_bio_updates'].rolling(window=3, min_periods=1).mean()
        
        return timeseries
    
    def get_age_wise_churn_analysis(self):
        """
        Detailed age-group breakdown of biometric churn.
        Task 4: Age-wise biometric churn analysis.
        """
        district_stats = self.df.groupby('district')[['bio_age_5_17', 'bio_age_17_']].sum()
        district_stats['total_bio_updates'] = district_stats.sum(axis=1)
        
        # Calculate age-wise percentages
        district_stats['youth_churn_pct'] = (district_stats['bio_age_5_17'] / district_stats['total_bio_updates']) * 100
        district_stats['adult_churn_pct'] = (district_stats['bio_age_17_'] / district_stats['total_bio_updates']) * 100
        
        # Calculate churn intensity
        district_stats['churn_intensity'] = district_stats['bio_age_17_'] / (district_stats['bio_age_5_17'] + 1)
        
        return district_stats.sort_values('churn_intensity', ascending=False)
    
    def get_volatility_metrics(self):
        """
        Measures biometric update stability over time.
        Task 4: Volatility metrics.
        """
        # Ensure month column exists
        if 'month' not in self.df.columns:
            if 'date' in self.df.columns:
                self.df['date'] = pd.to_datetime(self.df['date'])
                self.df['month'] = self.df['date'].dt.to_period('M').astype(str)
        
        # Calculate volatility per district
        district_monthly = self.df.groupby(['district', 'month'])[['bio_age_5_17', 'bio_age_17_']].sum()
        district_monthly['total_bio_updates'] = district_monthly.sum(axis=1)
        
        volatility = district_monthly.groupby('district')['total_bio_updates'].apply(
            lambda x: x.std() / (x.mean() + 1)
        )
        
        result = pd.DataFrame({
            'district': volatility.index,
            'bio_volatility': volatility.values,
            'stability_level': pd.cut(volatility.values, bins=[0, 0.3, 0.6, float('inf')], labels=['Stable', 'Moderate', 'Volatile'])
        }).sort_values('bio_volatility', ascending=False)
        
        return result
    
    def get_degradation_risk_zones(self, threshold=0.75):
        """
        Identifies high-stress occupational areas with fingerprint degradation risk.
        Task 4: Fingerprint degradation risk zones.
        
        Args:
            threshold: Adult biometric stress percentile threshold (default: 0.75)
        """
        stress_df = self.get_biometric_stress_index()
        
        # Identify high-risk zones (top 25% by default)
        risk_threshold = stress_df['biometric_stress_index'].quantile(threshold)
        high_risk = stress_df[stress_df['biometric_stress_index'] >= risk_threshold].copy()
        
        high_risk['risk_level'] = pd.cut(
            high_risk['biometric_stress_index'],
            bins=[risk_threshold, stress_df['biometric_stress_index'].quantile(0.85), 
                  stress_df['biometric_stress_index'].quantile(0.95), float('inf')],
            labels=['Moderate Risk', 'High Risk', 'Critical Risk']
        )
        
        return high_risk.sort_values('biometric_stress_index', ascending=False)
    
    def get_modality_recommendations(self):
        """
        Prioritizes iris vs fingerprint based on degradation patterns.
        Task 4: Modality prioritization insights.
        
        Returns:
            DataFrame with recommendations:
            - 'Prioritize Iris': High fingerprint degradation risk
            - 'Fingerprint OK': Low degradation risk
            - 'Monitor': Moderate risk
        """
        stress_df = self.get_biometric_stress_index()
        churn_df = self.get_age_wise_churn_analysis()
        
        # Merge analyses
        merged = stress_df[['biometric_stress_index']].join(
            churn_df[['churn_intensity']], how='outer'
        ).fillna(0)
        
        def recommend(row):
            high_stress = row['biometric_stress_index'] > merged['biometric_stress_index'].quantile(0.75)
            high_churn = row['churn_intensity'] > merged['churn_intensity'].quantile(0.75)
            
            if high_stress and high_churn:
                return 'Prioritize Iris'
            elif high_stress or high_churn:
                return 'Monitor'
            else:
                return 'Fingerprint OK'
        
        merged['recommendation'] = merged.apply(recommend, axis=1)
        
        return merged.sort_values('biometric_stress_index', ascending=False)

if __name__ == "__main__":
    # Test with combined biometric data
    import os
    base_path = r'c:\Users\mahad\OneDrive\Desktop\UIDAI'
    df = pd.read_csv(os.path.join(base_path, 'processed_data', 'biometric_combined.csv'))
    analytics = BiometricAnalytics(df)
    print("Biometric Stress Index Sample:")
    print(analytics.get_biometric_stress_index().head())
