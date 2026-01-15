import pandas as pd
import numpy as np

class EnrollmentAnalytics:
    def __init__(self, df):
        self.df = df
        # Pre-compute common derived columns
        age_cols = ['age_0_5', 'age_5_17', 'age_18_greater']
        if all(col in self.df.columns for col in age_cols):
            self.df['total_enrolment'] = self.df[age_cols].sum(axis=1)

    def get_total_enrolments(self):
        """Computes total enrolments per month."""
        # Summing age groups
        age_cols = ['age_0_5', 'age_5_17', 'age_18_greater']
        self.df['total_enrolment'] = self.df[age_cols].sum(axis=1)
        
        monthly_trends = self.df.groupby('month')['total_enrolment'].sum().reset_index()
        return monthly_trends

    def get_age_distribution(self):
        """Computes enrolment distribution across age groups."""
        age_cols = ['age_0_5', 'age_5_17', 'age_18_greater']
        dist = self.df[age_cols].sum().to_dict()
        return dist

    def get_district_inclusion_gaps_v2(self):
        """
        Identifies districts with high adult enrolment (potential inclusion gaps).
        Signals: 'Adult-dominant enrolment ratio'
        """
        # Group by district and age groups
        district_stats = self.df.groupby('district')[['age_0_5', 'age_5_17', 'age_18_greater']].sum()
        district_stats['total'] = district_stats.sum(axis=1)
        
        # Avoid division by zero
        district_stats = district_stats[district_stats['total'] > 0]
        
        district_stats['adult_dominance_ratio'] = district_stats['age_18_greater'] / district_stats['total']
        
        # Child inclusion gaps (age_0_5 / total) - Lower might mean child outreach needed
        district_stats['child_enrolment_ratio'] = district_stats['age_0_5'] / district_stats['total']
        
        return district_stats.sort_values('adult_dominance_ratio', ascending=False)

    def get_temporal_signals(self):
        """Detects seasonal spikes or MOM growth."""
        monthly = self.get_total_enrolments()
        monthly['mom_growth'] = monthly['total_enrolment'].pct_change() * 100
        return monthly
    
    def get_rolling_trends(self, window_3m=3, window_6m=6):
        """
        Computes rolling averages for trend smoothing.
        Task 1: Time-series aggregation with rolling windows.
        """
        monthly = self.get_total_enrolments()
        monthly[f'rolling_{window_3m}m'] = monthly['total_enrolment'].rolling(window=window_3m, min_periods=1).mean()
        monthly[f'rolling_{window_6m}m'] = monthly['total_enrolment'].rolling(window=window_6m, min_periods=1).mean()
        return monthly
    
    def classify_inclusion_risk(self):
        """
        Threshold-based classification for inclusion risk.
        Task 1: Statistical trend analysis + threshold classification.
        
        Risk Levels:
        - Low: Adult dominance ratio < 0.6
        - Medium: 0.6 <= ratio < 0.75
        - High: ratio >= 0.75
        """
        district_stats = self.get_district_inclusion_gaps_v2()
        
        def classify_risk(ratio):
            if ratio < 0.6:
                return 'Low'
            elif ratio < 0.75:
                return 'Medium'
            else:
                return 'High'
        
        district_stats['inclusion_risk_level'] = district_stats['adult_dominance_ratio'].apply(classify_risk)
        return district_stats
    
    def detect_late_enrollment_regions(self, threshold=0.7):
        """
        Identifies regions with high adult enrollment (late documentation).
        Task 1: Identification of late-enrollment regions.
        
        Args:
            threshold: Adult dominance ratio threshold (default: 0.7)
        """
        district_stats = self.get_district_inclusion_gaps_v2()
        late_enrollment = district_stats[district_stats['adult_dominance_ratio'] >= threshold].copy()
        late_enrollment['late_enrollment_flag'] = True
        return late_enrollment.sort_values('adult_dominance_ratio', ascending=False)
    
    def get_child_enrollment_gaps(self, threshold=0.05):
        """
        Highlights regions with low child enrollment (0-5 age group).
        Task 1: Detection of child enrollment gaps.
        
        Args:
            threshold: Minimum acceptable child enrollment ratio (default: 0.05 = 5%)
        """
        district_stats = self.get_district_inclusion_gaps_v2()
        child_gaps = district_stats[district_stats['child_enrolment_ratio'] < threshold].copy()
        child_gaps['child_gap_severity'] = (threshold - child_gaps['child_enrolment_ratio']) / threshold
        return child_gaps.sort_values('child_gap_severity', ascending=False)
    
    def get_yoy_growth(self):
        """
        Calculates Year-over-Year growth rates.
        Task 1: Enhanced temporal analysis.
        """
        if 'date' not in self.df.columns:
            return pd.DataFrame()
        
        # Ensure date is datetime
        self.df['date'] = pd.to_datetime(self.df['date'])
        self.df['year_month'] = self.df['date'].dt.to_period('M')
        
        monthly = self.df.groupby('year_month')[['age_0_5', 'age_5_17', 'age_18_greater']].sum()
        monthly['total_enrolment'] = monthly.sum(axis=1)
        
        # YoY growth (12 months ago)
        monthly['yoy_growth'] = monthly['total_enrolment'].pct_change(periods=12) * 100
        
        return monthly.reset_index()

if __name__ == "__main__":
    # Test with combined data
    import os
    base_path = r'c:\Users\mahad\OneDrive\Desktop\UIDAI'
    df = pd.read_csv(os.path.join(base_path, 'processed_data', 'enrollment_combined.csv'))
    df['date'] = pd.to_datetime(df['date'])
    
    analytics = EnrollmentAnalytics(df)
    print("Monthly Enrolment Trends:")
    print(analytics.get_total_enrolments().head())
    print("\nTop Districts by Adult Dominance (Inclusion Gap Signal):")
    print(analytics.get_district_inclusion_gaps_v2().head())
