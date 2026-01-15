from sklearn.preprocessing import MinMaxScaler
import pandas as pd
import numpy as np

class PriorityScorer:
    """
    Ranks PIN codes based on a multi-factor scoring algorithm.
    """
    
    def __init__(self, gap_weight=0.4, gap_pct_weight=0.4, volume_weight=0.2):
        self.gap_weight = gap_weight
        self.gap_pct_weight = gap_pct_weight
        self.volume_weight = volume_weight
        self.scaler = MinMaxScaler()

    def calculate_priority_scores(self, gap_df):
        """
        FR-3.1: Multi-Factor Scoring
        Calculates composite priority score and ranks PIN codes.
        """
        if gap_df.empty:
            return gap_df
            
        df = gap_df.copy()
        
        # Prepare metrics for normalization
        metrics = ['update_gap', 'gap_percentage', 'total_expected']
        
        # Handle cases with only one row or constant values for scaling
        if len(df) > 1:
            try:
                normalized_vals = self.scaler.fit_transform(df[metrics])
                df['gap_score_norm'] = normalized_vals[:, 0]
                df['gap_pct_score_norm'] = normalized_vals[:, 1]
                df['volume_score_norm'] = normalized_vals[:, 2]
            except Exception as e:
                print(f"Scaling error: {e}")
                df['gap_score_norm'] = 0.5
                df['gap_pct_score_norm'] = 0.5
                df['volume_score_norm'] = 0.5
        else:
            df['gap_score_norm'] = 1.0
            df['gap_pct_score_norm'] = 1.0
            df['volume_score_norm'] = 1.0

        # Weighted composite score
        df['priority_score'] = (
            self.gap_weight * df['gap_score_norm'] +
            self.gap_pct_weight * df['gap_pct_score_norm'] +
            self.volume_weight * df['volume_score_norm']
        ) * 100
        
        # Rank PIN codes
        df['priority_rank'] = df['priority_score'].rank(ascending=False, method='min').astype(int)
        
        # Assign Action Categories (simplified)
        def assign_action(row):
            if row['priority_rank'] <= 10: return 'Deploy Unit'
            if row['risk_level'] == 'Critical': return 'Intensive Drive'
            if row['risk_level'] == 'High': return 'Awareness Drive'
            return 'Monitor'
            
        df['recommended_action'] = df.apply(assign_action, axis=1)
        
        return df.sort_values('priority_rank')

    def model_intervention_resources(self, df):
        """
        Tactical Detail: Estimates resources needed to close the gap.
        Assuming 1 Mobile Van can process 50 children/day.
        Target: Close gap in 180 days (6 months).
        """
        if df.empty:
            return df
            
        # Resources = Gap / (Daily Capacity * Days)
        df['estimated_vans_needed'] = (df['update_gap'] / (50 * 180)).round(2)
        df['urgency_index'] = (df['priority_score'] * (1 + (df['estimated_vans_needed']/10))).clip(0, 100)
        
        return df
