import pandas as pd
import numpy as np

class MigrationAnalytics:
    def __init__(self, df):
        self.df = df
        # Pre-compute common derived columns
        update_cols = ['demo_age_5_17', 'demo_age_17_']
        if all(col in self.df.columns for col in update_cols):
            self.df['total_updates'] = self.df[update_cols].sum(axis=1)

    def get_update_intensity(self):
        """Computes total address updates per period."""
        # Note: In the demographic dataset, we have demo_age_5_17 and demo_age_17_
        # These represent demographic updates (which include address, name, etc.)
        self.df['total_updates'] = self.df[['demo_age_5_17', 'demo_age_17_']].sum(axis=1)
        
        intensity = self.df.groupby('month')['total_updates'].sum().reset_index()
        return intensity

    def get_migration_hotspots(self):
        """Identifies districts with disproportionately high update rates."""
        district_stats = self.df.groupby('district')['total_updates'].sum().reset_index()
        district_stats = district_stats.sort_values('total_updates', ascending=False)
        
        # Calculate Migration Intensity Index (Z-score of updates)
        mean_v = district_stats['total_updates'].mean()
        std_v = district_stats['total_updates'].std()
        district_stats['migration_intensity_index'] = (district_stats['total_updates'] - mean_v) / std_v
        
        return district_stats

    def detect_seasonal_migration(self):
        """Detects short-term spikes (volatility) in updates."""
        # Pivot by district and month
        pivot_df = self.df.pivot_table(index='month', columns='district', values='total_updates', aggfunc='sum').fillna(0)
        
        # Compute volatility (CV - Coefficient of Variation) for each district
        cv = pivot_df.apply(lambda x: x.std() / x.mean() if x.mean() > 0 else 0)
        volatility_df = cv.sort_values(ascending=False).reset_index()
        volatility_df.columns = ['district', 'update_volatility']
        
        return volatility_df
    
    def get_rolling_zscore_analysis(self, window=6):
        """
        Rolling Z-score analysis for time-series anomaly detection.
        Task 2: Time-series anomaly detection using rolling windows.
        
        Args:
            window: Rolling window size in months (default: 6)
        """
        # Ensure we have month column
        if 'month' not in self.df.columns:
            if 'date' in self.df.columns:
                self.df['date'] = pd.to_datetime(self.df['date'])
                self.df['month'] = self.df['date'].dt.to_period('M').astype(str)
        
        # Pivot by district and month
        pivot_df = self.df.pivot_table(index='month', columns='district', values='total_updates', aggfunc='sum').fillna(0)
        
        # Calculate rolling Z-scores for each district
        rolling_mean = pivot_df.rolling(window=window, min_periods=1).mean()
        rolling_std = pivot_df.rolling(window=window, min_periods=1).std()
        
        z_scores = (pivot_df - rolling_mean) / (rolling_std + 1e-6)
        
        # Get latest Z-scores
        latest_zscores = z_scores.iloc[-1].sort_values(ascending=False)
        
        result = pd.DataFrame({
            'district': latest_zscores.index,
            'rolling_zscore': latest_zscores.values,
            'anomaly_flag': latest_zscores.abs() > 2.0
        })
        
        return result
    
    def compare_windows(self, short_window=3, long_window=12):
        """
        Compares short-window vs long-window update rates.
        Task 2: Short-window vs long-window comparison for migration detection.
        
        Args:
            short_window: Recent period in months (default: 3)
            long_window: Historical baseline in months (default: 12)
        """
        # Ensure month column exists
        if 'month' not in self.df.columns:
            if 'date' in self.df.columns:
                self.df['date'] = pd.to_datetime(self.df['date'])
                self.df['month'] = self.df['date'].dt.to_period('M').astype(str)
        
        # Pivot by district and month
        pivot_df = self.df.pivot_table(index='month', columns='district', values='total_updates', aggfunc='sum').fillna(0)
        
        # Calculate short and long window averages
        short_avg = pivot_df.tail(short_window).mean()
        long_avg = pivot_df.tail(long_window).mean()
        
        # Calculate ratio
        window_ratio = short_avg / (long_avg + 1)
        
        result = pd.DataFrame({
            'district': window_ratio.index,
            'short_window_avg': short_avg.values,
            'long_window_avg': long_avg.values,
            'acceleration_ratio': window_ratio.values,
            'surge_detected': window_ratio.values > 1.5
        }).sort_values('acceleration_ratio', ascending=False)
        
        return result
    
    def get_normalized_migration_index(self):
        """
        Enhanced Migration Intensity Index with 0-100 normalization.
        Task 2: Index construction (Migration Intensity Index).
        """
        district_stats = self.get_migration_hotspots()
        
        # Normalize to 0-100 scale
        min_val = district_stats['migration_intensity_index'].min()
        max_val = district_stats['migration_intensity_index'].max()
        
        district_stats['migration_index_normalized'] = (
            (district_stats['migration_intensity_index'] - min_val) / (max_val - min_val + 1e-6) * 100
        )
        
        return district_stats
    
    def get_update_surge_alerts(self, threshold=2.0):
        """
        Detects sudden spikes in update volumes.
        Task 2: Update surge alerts using statistical thresholds.
        
        Args:
            threshold: Z-score threshold for surge detection (default: 2.0)
        """
        zscore_df = self.get_rolling_zscore_analysis()
        surges = zscore_df[zscore_df['rolling_zscore'] > threshold].copy()
        
        surges['severity'] = pd.cut(
            surges['rolling_zscore'],
            bins=[threshold, 2.5, 3.0, float('inf')],
            labels=['Moderate', 'High', 'Critical']
        )
        
        return surges.sort_values('rolling_zscore', ascending=False)
    
    def classify_migration_type(self):
        """
        Distinguishes seasonal vs sustained migration patterns.
        Task 2: Migration pattern classification.
        
        Returns:
            DataFrame with migration type classification:
            - 'Seasonal': High volatility, low sustained growth
            - 'Sustained': Low volatility, high sustained growth
            - 'Mixed': Both patterns present
            - 'Stable': Neither pattern
        """
        volatility_df = self.detect_seasonal_migration()
        window_df = self.compare_windows()
        
        # Merge both analyses
        merged = volatility_df.merge(window_df[['district', 'acceleration_ratio']], on='district', how='outer').fillna(0)
        
        def classify(row):
            high_volatility = row['update_volatility'] > 0.5
            high_acceleration = row['acceleration_ratio'] > 1.3
            
            if high_volatility and high_acceleration:
                return 'Mixed'
            elif high_volatility:
                return 'Seasonal'
            elif high_acceleration:
                return 'Sustained'
            else:
                return 'Stable'
        
        merged['migration_type'] = merged.apply(classify, axis=1)
        
        return merged.sort_values('update_volatility', ascending=False)

if __name__ == "__main__":
    import os
    # Test with combined demographic data
    base_path = r'c:\Users\mahad\OneDrive\Desktop\UIDAI'
    df = pd.read_csv(os.path.join(base_path, 'processed_data', 'demographic_combined.csv'))
    df['date'] = pd.to_datetime(df['date'])
    df['month'] = df['date'].dt.to_period('M').astype(str)
    
    analytics = MigrationAnalytics(df)
    print("Migration Intensity Index Sample:")
    print(analytics.get_migration_hotspots().head())
    print("\nUpdate Volatility (Seasonal Migration Signal):")
    print(analytics.detect_seasonal_migration().head())
