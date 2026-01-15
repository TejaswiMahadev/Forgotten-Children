import pandas as pd
import numpy as np
from scipy import stats

class ForecastingEngine:
    """
    Short-term demand forecasting for Aadhaar datasets.
    Task 6: Explainable forecasting using trend extrapolation and rolling windows.
    """
    
    def __init__(self, df, value_column='total_enrolment'):
        """
        Initialize forecasting engine.
        
        Args:
            df: DataFrame with time-series data (must have 'month' or 'date' column)
            value_column: Column to forecast
        """
        self.df = df.copy()
        self.value_column = value_column
        
        # Ensure we have a proper time index
        if 'month' in self.df.columns:
            self.df['month'] = pd.to_datetime(self.df['month'].astype(str))
            self.df = self.df.sort_values('month')
        elif 'date' in self.df.columns:
            self.df['date'] = pd.to_datetime(self.df['date'])
            self.df['month'] = self.df['date'].dt.to_period('M').dt.to_timestamp()
            self.df = self.df.sort_values('month')
    
    def forecast_enrollment(self, district=None, horizon=3):
        """
        Trend extrapolation for enrollment forecasting.
        Task 6: Next-month / next-quarter demand projections.
        
        Args:
            district: Specific district to forecast (None for national)
            horizon: Number of months to forecast (default: 3)
        
        Returns:
            DataFrame with forecasted values and confidence bands
        """
        # Filter by district if specified
        if district:
            data = self.df[self.df['district'] == district].copy()
        else:
            data = self.df.copy()
        
        # Aggregate by month
        if 'month' in data.columns:
            monthly = data.groupby('month')[self.value_column].sum().reset_index()
        else:
            return pd.DataFrame()
        
        # Fit linear trend
        monthly['time_index'] = range(len(monthly))
        X = monthly['time_index'].values
        y = monthly[self.value_column].values
        
        # Linear regression
        slope, intercept, r_value, p_value, std_err = stats.linregress(X, y)
        
        # Generate forecast
        last_index = len(monthly)
        future_indices = range(last_index, last_index + horizon)
        forecast_values = [slope * i + intercept for i in future_indices]
        
        # Create forecast DataFrame
        last_month = monthly['month'].iloc[-1]
        future_months = pd.date_range(start=last_month, periods=horizon + 1, freq='MS')[1:]
        
        forecast_df = pd.DataFrame({
            'month': future_months,
            'forecast': forecast_values,
            'trend_slope': slope,
            'r_squared': r_value ** 2
        })
        
        return forecast_df
    
    def forecast_updates(self, district=None, horizon=3):
        """
        Rolling window forecasting for demographic/biometric updates.
        Task 6: Rolling window forecasting.
        
        Args:
            district: Specific district to forecast (None for national)
            horizon: Number of months to forecast (default: 3)
        """
        # Filter by district if specified
        if district:
            data = self.df[self.df['district'] == district].copy()
        else:
            data = self.df.copy()
        
        # Aggregate by month
        if 'month' in data.columns:
            monthly = data.groupby('month')[self.value_column].sum().reset_index()
        else:
            return pd.DataFrame()
        
        # Use rolling average for forecast
        window = min(6, len(monthly))
        rolling_avg = monthly[self.value_column].rolling(window=window, min_periods=1).mean().iloc[-1]
        
        # Simple persistence forecast with slight trend adjustment
        recent_trend = monthly[self.value_column].iloc[-3:].mean() - monthly[self.value_column].iloc[-6:-3].mean()
        
        forecast_values = [rolling_avg + (i * recent_trend / 3) for i in range(1, horizon + 1)]
        
        # Create forecast DataFrame
        last_month = monthly['month'].iloc[-1]
        future_months = pd.date_range(start=last_month, periods=horizon + 1, freq='MS')[1:]
        
        forecast_df = pd.DataFrame({
            'month': future_months,
            'forecast': forecast_values,
            'baseline': rolling_avg
        })
        
        return forecast_df
    
    def get_confidence_bands(self, forecast_df, historical_data, confidence_level=0.95):
        """
        Calculate confidence intervals for forecasts.
        Task 6: Confidence band estimation.
        
        Args:
            forecast_df: DataFrame with forecast values
            historical_data: Historical data for error estimation
            confidence_level: Confidence level (default: 0.95)
        
        Returns:
            DataFrame with upper and lower confidence bounds
        """
        # Calculate historical forecast errors (using simple method)
        historical_std = historical_data[self.value_column].std()
        
        # Z-score for confidence level
        z_score = stats.norm.ppf((1 + confidence_level) / 2)
        
        # Add confidence bands
        forecast_df['lower_bound'] = forecast_df['forecast'] - (z_score * historical_std)
        forecast_df['upper_bound'] = forecast_df['forecast'] + (z_score * historical_std)
        
        # Ensure non-negative forecasts
        forecast_df['lower_bound'] = forecast_df['lower_bound'].clip(lower=0)
        forecast_df['forecast'] = forecast_df['forecast'].clip(lower=0)
        
        return forecast_df
    
    def generate_capacity_signals(self, forecast_df, current_capacity=None):
        """
        Translate forecasts into infrastructure planning signals.
        Task 6: Capacity planning signals.
        
        Args:
            forecast_df: DataFrame with forecast values
            current_capacity: Current system capacity (optional)
        
        Returns:
            DataFrame with capacity planning recommendations
        """
        forecast_df = forecast_df.copy()
        
        # Calculate growth rate
        forecast_df['growth_rate'] = forecast_df['forecast'].pct_change() * 100
        
        # Generate signals
        def generate_signal(row):
            if pd.isna(row['growth_rate']):
                return 'Baseline'
            elif row['growth_rate'] > 20:
                return 'High Demand - Scale Up'
            elif row['growth_rate'] > 10:
                return 'Moderate Growth - Monitor'
            elif row['growth_rate'] < -10:
                return 'Declining - Optimize'
            else:
                return 'Stable - Maintain'
        
        forecast_df['capacity_signal'] = forecast_df.apply(generate_signal, axis=1)
        
        # If capacity is provided, calculate utilization
        if current_capacity:
            forecast_df['projected_utilization'] = (forecast_df['forecast'] / current_capacity) * 100
            forecast_df['capacity_alert'] = forecast_df['projected_utilization'] > 80
        
        return forecast_df
    
    def compare_forecast_vs_actual(self, forecast_df, actual_df):
        """
        Validation method for forecast accuracy.
        Task 6: Forecast validation.
        
        Args:
            forecast_df: DataFrame with forecasted values
            actual_df: DataFrame with actual values
        
        Returns:
            Dictionary with accuracy metrics (MAPE, RMSE)
        """
        # Merge forecast and actual
        merged = forecast_df.merge(actual_df, on='month', how='inner', suffixes=('_forecast', '_actual'))
        
        if len(merged) == 0:
            return {'error': 'No overlapping data for validation'}
        
        # Calculate metrics
        actual_values = merged[f'{self.value_column}_actual'].values
        forecast_values = merged['forecast'].values
        
        # Mean Absolute Percentage Error
        mape = np.mean(np.abs((actual_values - forecast_values) / (actual_values + 1))) * 100
        
        # Root Mean Squared Error
        rmse = np.sqrt(np.mean((actual_values - forecast_values) ** 2))
        
        # Mean Absolute Error
        mae = np.mean(np.abs(actual_values - forecast_values))
        
        return {
            'MAPE': mape,
            'RMSE': rmse,
            'MAE': mae,
            'num_observations': len(merged)
        }

if __name__ == "__main__":
    # Test with sample data
    import os
    base_path = r'c:\Users\mahad\OneDrive\Desktop\UIDAI'
    df = pd.read_csv(os.path.join(base_path, 'processed_data', 'enrollment_combined.csv'))
    df['date'] = pd.to_datetime(df['date'])
    
    # Calculate total enrollment
    df['total_enrolment'] = df[['age_0_5', 'age_5_17', 'age_18_greater']].sum(axis=1)
    
    # Initialize forecasting engine
    engine = ForecastingEngine(df, value_column='total_enrolment')
    
    print("National Enrollment Forecast (Next 3 Months):")
    forecast = engine.forecast_enrollment(horizon=3)
    print(forecast)
    
    print("\nWith Confidence Bands:")
    forecast_with_ci = engine.get_confidence_bands(forecast, df)
    print(forecast_with_ci)
    
    print("\nCapacity Planning Signals:")
    capacity_signals = engine.generate_capacity_signals(forecast_with_ci)
    print(capacity_signals)
