import pandas as pd
import datetime

class ReportGenerator:
    """
    Generates summary reports and export-ready datasets.
    """
    
    @staticmethod
    def generate_executive_summary(gap_df, forecast_df, anomaly_df):
        """
        Creates a dictionary of metrics for an executive report.
        """
        if gap_df.empty:
            return "No data available."
            
        summary = {
            'timestamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
            'total_children_impacted': int(gap_df['update_gap'].sum()),
            'avg_update_rate': f"{gap_df['update_rate'].mean():.1f}%",
            'critical_areas_count': int((gap_df['risk_level'] == 'Critical').sum()),
            'predicted_future_gap': int(forecast_df['predicted_future_gap'].sum()) if not forecast_df.empty else 0,
            'anomalies_detected': len(anomaly_df) if not anomaly_df.empty else 0
        }
        
        return summary

    @staticmethod
    def get_priority_list(gap_df, top_n=20):
        """
        Returns a formatted dataframe of top priority areas.
        """
        if gap_df.empty:
            return gap_df
            
        cols = ['priority_rank', 'pincode', 'district', 'update_gap', 'update_rate', 'risk_level', 'recommended_action']
        return gap_df[cols].head(top_n)
