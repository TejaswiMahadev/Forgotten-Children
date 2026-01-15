import pandas as pd
import numpy as np

class IntelligenceEngine:
    def __init__(self, enrollment_df, demographic_df, biometric_df):
        self.e_df = enrollment_df
        self.d_df = demographic_df
        self.b_df = biometric_df

    def get_inclusion_risk_index(self):
        """
        Fuses enrolment and biometric stress signals.
        Risk = (Adult Enrolment Ratio) + (Biometric Churn)
        """
        # Enrollment signal
        e_stats = self.e_df.groupby('district')[['age_0_5', 'age_5_17', 'age_18_greater']].sum()
        e_stats['total_e'] = e_stats.sum(axis=1)
        e_stats['adult_e_ratio'] = e_stats['age_18_greater'] / e_stats['total_e']
        
        # Biometric signal
        b_stats = self.b_df.groupby('district')[['bio_age_5_17', 'bio_age_17_']].sum()
        b_stats['total_b'] = b_stats.sum(axis=1)
        b_stats['bio_stress'] = b_stats['bio_age_17_'] / b_stats['total_b']
        
        # Merge
        risk_df = e_stats[['adult_e_ratio']].join(b_stats[['bio_stress']], how='outer').fillna(0)
        
        # Normalized Inclusion Risk Index (0 to 1)
        risk_df['inclusion_risk_index'] = (risk_df['adult_e_ratio'] + risk_df['bio_stress']) / 2
        
        return risk_df.sort_values('inclusion_risk_index', ascending=False)

    def get_system_stress_index(self):
        """
        Predicts infrastructure load.
        Stress = (Monthly Enrolment growth) + (Update intensity)
        """
        # Combine total transactions per district/month
        e_load = self.e_df.groupby(['month', 'district'])[['age_0_5', 'age_5_17', 'age_18_greater']].sum().sum(axis=1)
        d_load = self.d_df.groupby(['month', 'district'])[['demo_age_5_17', 'demo_age_17_']].sum().sum(axis=1)
        b_load = self.b_df.groupby(['month', 'district'])[['bio_age_5_17', 'bio_age_17_']].sum().sum(axis=1)
        
        total_load = pd.DataFrame({'e': e_load, 'd': d_load, 'b': b_load}).fillna(0)
        total_load['combined_load'] = total_load.sum(axis=1)
        
        # Anomaly Detection: Z-score of combined load per district
        total_load = total_load.reset_index()
        district_mean = total_load.groupby('district')['combined_load'].transform('mean')
        district_std = total_load.groupby('district')['combined_load'].transform('std')
        total_load['system_stress_index'] = (total_load['combined_load'] - district_mean) / (district_std + 1)
        
        return total_load

    def detect_anomalies(self):
        """Statistical outlier detection across all signals."""
        stress = self.get_system_stress_index()
        # Label anomalies as "Operational" if stress index > 2 (threshold)
        stress['is_anomaly'] = stress['system_stress_index'] > 2
        return stress[stress['is_anomaly']]
    
    def align_temporal_data(self):
        """
        Ensures all datasets use consistent time ranges.
        Task 5: Temporal alignment of datasets.
        
        Returns:
            Dictionary with aligned datasets
        """
        # Get common date range
        e_dates = set(self.e_df['month'].unique()) if 'month' in self.e_df.columns else set()
        d_dates = set(self.d_df['month'].unique()) if 'month' in self.d_df.columns else set()
        b_dates = set(self.b_df['month'].unique()) if 'month' in self.b_df.columns else set()
        
        common_dates = e_dates.intersection(d_dates).intersection(b_dates)
        
        # Filter to common dates
        e_aligned = self.e_df[self.e_df['month'].isin(common_dates)] if 'month' in self.e_df.columns else self.e_df
        d_aligned = self.d_df[self.d_df['month'].isin(common_dates)] if 'month' in self.d_df.columns else self.d_df
        b_aligned = self.b_df[self.b_df['month'].isin(common_dates)] if 'month' in self.b_df.columns else self.b_df
        
        return {
            'enrollment': e_aligned,
            'demographic': d_aligned,
            'biometric': b_aligned,
            'common_months': sorted(list(common_dates))
        }
    
    def get_correlation_matrix(self):
        """
        Cross-dataset signal correlation analysis.
        Task 5: Correlation and co-movement analysis.
        
        Returns:
            DataFrame with correlation coefficients
        """
        # Aggregate by district
        e_stats = self.e_df.groupby('district')[['age_0_5', 'age_5_17', 'age_18_greater']].sum()
        e_stats['total_enrollment'] = e_stats.sum(axis=1)
        
        d_stats = self.d_df.groupby('district')[['demo_age_5_17', 'demo_age_17_']].sum()
        d_stats['total_demo_updates'] = d_stats.sum(axis=1)
        
        b_stats = self.b_df.groupby('district')[['bio_age_5_17', 'bio_age_17_']].sum()
        b_stats['total_bio_updates'] = b_stats.sum(axis=1)
        
        # Merge all
        merged = e_stats[['total_enrollment']].join(
            d_stats[['total_demo_updates']], how='outer'
        ).join(
            b_stats[['total_bio_updates']], how='outer'
        ).fillna(0)
        
        # Calculate correlation matrix
        correlation = merged.corr()
        
        return correlation
    
    def get_comovement_analysis(self):
        """
        Detects synchronized patterns across datasets.
        Task 5: Co-movement analysis.
        
        Returns:
            DataFrame with co-movement indicators
        """
        # Aggregate by month and district
        e_monthly = self.e_df.groupby(['month', 'district'])[['age_0_5', 'age_5_17', 'age_18_greater']].sum()
        e_monthly['total_e'] = e_monthly.sum(axis=1)
        
        d_monthly = self.d_df.groupby(['month', 'district'])[['demo_age_5_17', 'demo_age_17_']].sum()
        d_monthly['total_d'] = d_monthly.sum(axis=1)
        
        # Merge
        merged = e_monthly[['total_e']].join(d_monthly[['total_d']], how='inner')
        
        # Calculate period-over-period changes
        merged = merged.reset_index().sort_values(['district', 'month'])
        merged['e_change'] = merged.groupby('district')['total_e'].pct_change()
        merged['d_change'] = merged.groupby('district')['total_d'].pct_change()
        
        # Identify co-movement (both increasing or both decreasing)
        merged['comovement'] = (
            ((merged['e_change'] > 0) & (merged['d_change'] > 0)) |
            ((merged['e_change'] < 0) & (merged['d_change'] < 0))
        )
        
        # Aggregate co-movement by district
        comovement_stats = merged.groupby('district')['comovement'].agg(['sum', 'count'])
        comovement_stats['comovement_ratio'] = comovement_stats['sum'] / comovement_stats['count']
        
        return comovement_stats.sort_values('comovement_ratio', ascending=False)
    
    def get_weighted_inclusion_risk_index(self):
        """
        Enhanced Inclusion Risk Index with weighted scoring.
        Task 5: Weighted scoring (enrollment: 40%, biometric: 30%, demographic: 30%).
        
        Returns:
            DataFrame with weighted inclusion risk scores
        """
        # Enrollment signal (40% weight)
        e_stats = self.e_df.groupby('district')[['age_0_5', 'age_5_17', 'age_18_greater']].sum()
        e_stats['total_e'] = e_stats.sum(axis=1)
        e_stats['adult_e_ratio'] = e_stats['age_18_greater'] / e_stats['total_e']
        
        # Normalize to 0-1
        e_stats['adult_e_ratio_norm'] = (
            (e_stats['adult_e_ratio'] - e_stats['adult_e_ratio'].min()) /
            (e_stats['adult_e_ratio'].max() - e_stats['adult_e_ratio'].min() + 1e-6)
        )
        
        # Biometric signal (30% weight)
        b_stats = self.b_df.groupby('district')[['bio_age_5_17', 'bio_age_17_']].sum()
        b_stats['total_b'] = b_stats.sum(axis=1)
        b_stats['bio_stress'] = b_stats['bio_age_17_'] / b_stats['total_b']
        
        # Normalize to 0-1
        b_stats['bio_stress_norm'] = (
            (b_stats['bio_stress'] - b_stats['bio_stress'].min()) /
            (b_stats['bio_stress'].max() - b_stats['bio_stress'].min() + 1e-6)
        )
        
        # Demographic signal (30% weight)
        d_stats = self.d_df.groupby('district')[['demo_age_5_17', 'demo_age_17_']].sum()
        d_stats['total_d'] = d_stats.sum(axis=1)
        d_stats['demo_stress'] = d_stats['demo_age_17_'] / d_stats['total_d']
        
        # Normalize to 0-1
        d_stats['demo_stress_norm'] = (
            (d_stats['demo_stress'] - d_stats['demo_stress'].min()) /
            (d_stats['demo_stress'].max() - d_stats['demo_stress'].min() + 1e-6)
        )
        
        # Merge all
        risk_df = e_stats[['adult_e_ratio_norm']].join(
            b_stats[['bio_stress_norm']], how='outer'
        ).join(
            d_stats[['demo_stress_norm']], how='outer'
        ).fillna(0)
        
        # Weighted scoring
        risk_df['weighted_inclusion_risk'] = (
            0.4 * risk_df['adult_e_ratio_norm'] +
            0.3 * risk_df['bio_stress_norm'] +
            0.3 * risk_df['demo_stress_norm']
        ) * 100  # Scale to 0-100
        
        return risk_df.sort_values('weighted_inclusion_risk', ascending=False)
    
    def classify_anomalies_enhanced(self):
        """
        Enhanced anomaly classification (Societal/Operational/Structural).
        Task 5: Anomaly classification.
        
        Returns:
            DataFrame with classified anomalies
        """
        anomalies = self.detect_anomalies()
        
        if anomalies.empty:
            return anomalies
        
        def classify(row):
            stress_level = row['system_stress_index']
            
            # Very high stress (>3) suggests operational issues
            if stress_level > 3:
                return 'Operational'
            # Moderate stress (2-3) could be societal
            elif stress_level > 2:
                return 'Societal'
            # Lower stress might be structural changes
            else:
                return 'Structural'
        
        anomalies['anomaly_classification'] = anomalies.apply(classify, axis=1)
        
        return anomalies

if __name__ == "__main__":
    import os
    base_path = r'c:\Users\mahad\OneDrive\Desktop\UIDAI'
    e_df = pd.read_csv(os.path.join(base_path, 'processed_data', 'enrollment_combined.csv'))
    d_df = pd.read_csv(os.path.join(base_path, 'processed_data', 'demographic_combined.csv'))
    b_df = pd.read_csv(os.path.join(base_path, 'processed_data', 'biometric_combined.csv'))
    
    engine = IntelligenceEngine(e_df, d_df, b_df)
    print("Inclusion Risk Index Sample:")
    print(engine.get_inclusion_risk_index().head())
    print("\nAnomalies Detected:")
    print(engine.detect_anomalies().head())
