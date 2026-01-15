import pandas as pd
import numpy as np
from scipy import stats

class AnomalyDetector:
    """
    Advanced anomaly detection with contextual classification.
    Task 7: Anomaly detection with societal, operational, and structural context.
    """
    
    def __init__(self, df):
        """
        Initialize anomaly detector.
        
        Args:
            df: DataFrame with time-series data
        """
        self.df = df.copy()
        
        # Ensure month column exists
        if 'month' not in self.df.columns:
            if 'date' in self.df.columns:
                self.df['date'] = pd.to_datetime(self.df['date'])
                self.df['month'] = self.df['date'].dt.to_period('M').astype(str)
    
    def detect_zscore_anomalies(self, column, threshold=2.5):
        """
        Statistical outlier detection using Z-scores.
        Task 7: Z-score based anomaly detection.
        
        Args:
            column: Column to analyze
            threshold: Z-score threshold (default: 2.5)
        
        Returns:
            DataFrame with anomalies flagged
        """
        if column not in self.df.columns:
            return pd.DataFrame()
        
        # Calculate Z-scores
        mean_val = self.df[column].mean()
        std_val = self.df[column].std()
        
        self.df['zscore'] = (self.df[column] - mean_val) / (std_val + 1e-6)
        self.df['is_anomaly_zscore'] = self.df['zscore'].abs() > threshold
        
        anomalies = self.df[self.df['is_anomaly_zscore']].copy()
        anomalies['detection_method'] = 'Z-Score'
        anomalies['severity'] = anomalies['zscore'].abs()
        
        return anomalies.sort_values('severity', ascending=False)
    
    def detect_iqr_anomalies(self, column):
        """
        Interquartile range-based anomaly detection.
        Task 7: IQR-based anomaly detection.
        
        Args:
            column: Column to analyze
        
        Returns:
            DataFrame with anomalies flagged
        """
        if column not in self.df.columns:
            return pd.DataFrame()
        
        # Calculate IQR
        Q1 = self.df[column].quantile(0.25)
        Q3 = self.df[column].quantile(0.75)
        IQR = Q3 - Q1
        
        # Define outlier bounds
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        
        self.df['is_anomaly_iqr'] = (self.df[column] < lower_bound) | (self.df[column] > upper_bound)
        
        anomalies = self.df[self.df['is_anomaly_iqr']].copy()
        anomalies['detection_method'] = 'IQR'
        anomalies['lower_bound'] = lower_bound
        anomalies['upper_bound'] = upper_bound
        
        return anomalies
    
    def detect_changepoints(self, column, window=6):
        """
        Identifies structural breaks in trends.
        Task 7: Change-point analysis.
        
        Args:
            column: Column to analyze
            window: Window size for change detection (default: 6)
        
        Returns:
            DataFrame with potential change points
        """
        if column not in self.df.columns or 'month' not in self.df.columns:
            return pd.DataFrame()
        
        # Sort by month
        df_sorted = self.df.sort_values('month').copy()
        
        # Calculate rolling mean and std
        df_sorted['rolling_mean'] = df_sorted[column].rolling(window=window, min_periods=1).mean()
        df_sorted['rolling_std'] = df_sorted[column].rolling(window=window, min_periods=1).std()
        
        # Detect significant changes
        df_sorted['mean_shift'] = df_sorted['rolling_mean'].diff().abs()
        df_sorted['is_changepoint'] = df_sorted['mean_shift'] > (2 * df_sorted['rolling_std'])
        
        changepoints = df_sorted[df_sorted['is_changepoint']].copy()
        changepoints['detection_method'] = 'Change-Point'
        
        return changepoints
    
    def check_temporal_consistency(self, column, max_change_pct=50):
        """
        Flags inconsistent patterns (e.g., sudden drops/spikes).
        Task 7: Temporal consistency checks.
        
        Args:
            column: Column to analyze
            max_change_pct: Maximum acceptable change percentage (default: 50%)
        
        Returns:
            DataFrame with inconsistencies flagged
        """
        if column not in self.df.columns or 'month' not in self.df.columns:
            return pd.DataFrame()
        
        # Sort by month
        df_sorted = self.df.sort_values('month').copy()
        
        # Calculate period-over-period change
        df_sorted['pct_change'] = df_sorted[column].pct_change() * 100
        df_sorted['is_inconsistent'] = df_sorted['pct_change'].abs() > max_change_pct
        
        inconsistencies = df_sorted[df_sorted['is_inconsistent']].copy()
        inconsistencies['detection_method'] = 'Temporal Inconsistency'
        
        return inconsistencies
    
    def classify_anomaly_type(self, anomaly_row):
        """
        Labels anomalies as Societal, Operational, or Structural.
        Task 7: Anomaly classification with context.
        
        Classification Logic:
        - Societal: Migration surges, festival-related spikes, demographic shifts
        - Operational: System downtime, processing delays, data quality issues
        - Structural: Policy changes, new enrollment centers, infrastructure expansion
        
        Args:
            anomaly_row: Single row from anomaly DataFrame
        
        Returns:
            String classification
        """
        # Check for temporal patterns
        if 'month' in anomaly_row.index:
            month_str = str(anomaly_row['month'])
            
            # Festival/seasonal patterns (Societal)
            if any(m in month_str for m in ['2025-09', '2025-10', '2025-11']):  # Festival season
                return 'Societal'
        
        # Check severity
        if 'severity' in anomaly_row.index:
            severity = anomaly_row['severity']
            
            # Very high severity might indicate operational issues
            if severity > 4:
                return 'Operational'
        
        # Check for change points (Structural)
        if 'is_changepoint' in anomaly_row.index and anomaly_row['is_changepoint']:
            return 'Structural'
        
        # Default to Societal for moderate anomalies
        return 'Societal'
    
    def generate_anomaly_context(self, anomaly_row):
        """
        Creates human-readable explanations for anomalies.
        Task 7: Contextual explanations.
        
        Args:
            anomaly_row: Single row from anomaly DataFrame
        
        Returns:
            String explanation
        """
        anomaly_type = self.classify_anomaly_type(anomaly_row)
        
        if anomaly_type == 'Societal':
            return "Potential migration surge or seasonal demographic shift. May be linked to festivals, harvest season, or labor mobility."
        elif anomaly_type == 'Operational':
            return "Possible system processing delay or data quality issue. Recommend investigating infrastructure logs."
        elif anomaly_type == 'Structural':
            return "Significant trend change detected. May indicate policy change, new enrollment centers, or infrastructure expansion."
        else:
            return "Anomaly detected. Further investigation recommended."
    
    def detect_all_anomalies(self, column, methods=['zscore', 'iqr', 'changepoint', 'consistency']):
        """
        Runs all anomaly detection methods and consolidates results.
        Task 7: Comprehensive anomaly detection.
        
        Args:
            column: Column to analyze
            methods: List of methods to use
        
        Returns:
            DataFrame with all detected anomalies and classifications
        """
        all_anomalies = []
        
        if 'zscore' in methods:
            zscore_anomalies = self.detect_zscore_anomalies(column)
            if not zscore_anomalies.empty:
                all_anomalies.append(zscore_anomalies)
        
        if 'iqr' in methods:
            iqr_anomalies = self.detect_iqr_anomalies(column)
            if not iqr_anomalies.empty:
                all_anomalies.append(iqr_anomalies)
        
        if 'changepoint' in methods:
            changepoint_anomalies = self.detect_changepoints(column)
            if not changepoint_anomalies.empty:
                all_anomalies.append(changepoint_anomalies)
        
        if 'consistency' in methods:
            consistency_anomalies = self.check_temporal_consistency(column)
            if not consistency_anomalies.empty:
                all_anomalies.append(consistency_anomalies)
        
        if not all_anomalies:
            return pd.DataFrame()
        
        # Consolidate
        consolidated = pd.concat(all_anomalies, ignore_index=True)
        
        # Add classifications
        consolidated['anomaly_type'] = consolidated.apply(self.classify_anomaly_type, axis=1)
        consolidated['context'] = consolidated.apply(self.generate_anomaly_context, axis=1)
        
        return consolidated.drop_duplicates(subset=['month', 'district'] if 'district' in consolidated.columns else ['month'])

if __name__ == "__main__":
    # Test with sample data
    import os
    base_path = r'c:\Users\mahad\OneDrive\Desktop\UIDAI'
    df = pd.read_csv(os.path.join(base_path, 'processed_data', 'enrollment_combined.csv'))
    df['date'] = pd.to_datetime(df['date'])
    
    # Calculate total enrollment
    df['total_enrolment'] = df[['age_0_5', 'age_5_17', 'age_18_greater']].sum(axis=1)
    
    # Initialize detector
    detector = AnomalyDetector(df)
    
    print("Z-Score Anomalies:")
    zscore_anomalies = detector.detect_zscore_anomalies('total_enrolment')
    print(zscore_anomalies[['month', 'district', 'total_enrolment', 'zscore']].head())
    
    print("\nAll Anomalies with Context:")
    all_anomalies = detector.detect_all_anomalies('total_enrolment')
    print(all_anomalies[['month', 'district', 'detection_method', 'anomaly_type', 'context']].head())
