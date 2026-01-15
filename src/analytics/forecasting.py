import pandas as pd
import numpy as np

class ForecastingEngine:
    """
    Predicts future biometric update gaps based on recent enrollments.
    """
    
    @staticmethod
    def forecast_future_gaps(enrollment_df, current_gap_df, forecast_horizon_years=3):
        """
        FR-5.1: Future Gap Forecasting
        Applies current update rates to predict future needs.
        """
        if enrollment_df.empty or current_gap_df.empty:
            return pd.DataFrame()
            
        # 1. Identify recent enrollments (0-5 age group from last 5 years)
        # Assuming current_date is 2025-12-31
        current_date = pd.Timestamp('2025-12-31')
        recent_cutoff = current_date - pd.DateOffset(years=5)
        
        recent_enroll = enrollment_df[enrollment_df['date'] >= recent_cutoff].copy()
        recent_agg = recent_enroll.groupby('pincode')['age_0_5'].sum().reset_index()
        recent_agg.columns = ['pincode', 'recent_enrollments_0_5']
        
        # 2. Get current update rates per PIN
        rates = current_gap_df[['pincode', 'update_rate']].copy()
        
        # 3. Forecast
        forecast = pd.merge(recent_agg, rates, on='pincode', how='left')
        forecast['update_rate'] = forecast['update_rate'].fillna(rates['update_rate'].mean())
        
        forecast['predicted_updates'] = (forecast['recent_enrollments_0_5'] * forecast['update_rate'] / 100).astype(int)
        forecast['predicted_future_gap'] = forecast['recent_enrollments_0_5'] - forecast['predicted_updates']
        
        # Forecasted Risk Level
        def assign_forecast_risk(gap_count, enroll_count):
            if enroll_count == 0: return 'Low'
            ratio = gap_count / enroll_count
            if ratio >= 0.7: return 'Critical'
            if ratio >= 0.5: return 'High'
            if ratio >= 0.3: return 'Medium'
            return 'Low'
            
        forecast['forecast_risk_level'] = forecast.apply(
            lambda x: assign_forecast_risk(x['predicted_future_gap'], x['recent_enrollments_0_5']), axis=1
        )
        
        # Confidence Intervals (Simple heuristic)
        forecast['conf_low'] = (forecast['predicted_future_gap'] * 0.9).astype(int)
        forecast['conf_high'] = (forecast['predicted_future_gap'] * 1.1).astype(int)
        
        return forecast.sort_values('predicted_future_gap', ascending=False)
