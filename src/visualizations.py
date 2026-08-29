import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import folium
from folium import plugins

# Risk Level Colors as per PRD
RISK_COLORS = {
    'Critical': '#D32F2F',
    'High': '#F57C00',
    'Medium': '#FBC02D',
    'Low': '#388E3C'
}

# Dash Professional Colors
DASH_BLUE = '#1d8cf8'
DASH_PINK = '#e14eca'
DASH_GREEN = '#00f2c3'
DASH_DARK = '#27293d'

def set_dark_theme(fig):
    """Applies Dash Professional styling to any figure"""
    fig.update_layout(
        template='plotly_dark',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font_color='#9a9a9a',
        margin=dict(l=20, r=20, t=40, b=20)
    )
    return fig

def create_geographic_mapbox(df):
    """Professional Mapbox visualization for Dash"""
    # District Level Fallback Coords (reused from previous logic)
    district_coords = {
        'Central Delhi': [28.6441, 77.2346], 'West Delhi': [28.6675, 77.0706],
        'North East Delhi': [28.6914, 77.2692], 'South West Delhi': [28.5733, 77.0105],
        'Hyderabad': [17.3850, 78.4867], 'Adilabad': [19.6641, 78.5320],
        'Chandigarh': [30.7333, 76.7794], 'Darbhanga': [26.1167, 85.8917],
        'Gadchiroli': [20.1000, 79.9833], 'Gaya': [24.7914, 85.0002],
        'Khammam': [17.2473, 80.1514], 'Kishanganj': [26.0717, 87.9383],
        'Mohali': [30.7046, 76.7179], 'Mumbai Suburban': [19.1264, 72.8567],
        'Muzaffarpur': [26.1209, 85.3647], 'Nizamabad': [18.6725, 78.0941],
        'Patna': [25.5941, 85.1376], 'Pune': [18.5204, 73.8567],
        'Purnia': [25.7771, 87.4753], 'Rangareddy': [17.3700, 78.4800],
        'Warangal': [17.9784, 79.5941]
    }
    
    import random
    map_df = df.copy()
    
    def get_coords(row):
        d = row['district']
        base = district_coords.get(d, [22.9734, 78.6569])
        # Add jitter
        return [base[0] + random.uniform(-0.05, 0.05), base[1] + random.uniform(-0.05, 0.05)]
    
    coords = map_df.apply(get_coords, axis=1)
    map_df['lat'] = [c[0] for c in coords]
    map_df['lon'] = [c[1] for c in coords]
    
    # Plotly 6.0 removed px.scatter_mapbox in favour of the MapLibre-backed
    # px.scatter_map. Support both so the map renders on any recent Plotly.
    scatter_fn = getattr(px, 'scatter_map', None)
    style_key = 'map_style'
    if scatter_fn is None:
        scatter_fn = px.scatter_mapbox
        style_key = 'mapbox_style'

    fig = scatter_fn(
        map_df, lat="lat", lon="lon", color="risk_level",
        size="update_gap", color_discrete_map=RISK_COLORS,
        hover_name="pincode", hover_data=["district", "update_rate"],
        zoom=4, height=500
    )
    fig.update_layout(**{style_key: "carto-darkmatter"})
    return set_dark_theme(fig)

def create_priority_bar_chart(df):
    """Horizontal bar chart of top priority PIN codes"""
    top_10 = df.head(10).sort_values('priority_score')
    fig = px.bar(
        top_10, 
        x='priority_score', 
        y='pincode', 
        orientation='h',
        color='risk_level',
        color_discrete_map=RISK_COLORS,
        title="Top 10 Priority PIN Codes by Score",
        labels={'priority_score': 'Priority Score', 'pincode': 'PIN Code'},
        hover_data=['district', 'update_gap', 'update_rate']
    )
    fig.update_layout(yaxis={'categoryorder':'total ascending'})
    return set_dark_theme(fig)

def create_gap_by_district_chart(df):
    """Bar chart showing total gap by district"""
    dist_df = df.groupby('district')['update_gap'].sum().reset_index()
    dist_df = dist_df.sort_values('update_gap', ascending=False)
    fig = px.bar(
        dist_df, 
        x='district', 
        y='update_gap',
        title="Total Biometric Update Gap by District",
        labels={'update_gap': 'Total Gap (Count)', 'district': 'District'},
        color='update_gap',
        color_continuous_scale='Reds'
    )
    return set_dark_theme(fig)

def create_temporal_line_chart(monthly_trend):
    """Time series of update trends"""
    fig = px.line(
        monthly_trend, 
        x='year_month', 
        y='bio_age_5_17',
        title="Biometric Update Trend (5-17 Age Group)",
        labels={'bio_age_5_17': 'Updates Count', 'year_month': 'Month'},
        markers=True
    )
    fig.update_layout(xaxis_tickangle=-45)
    return set_dark_theme(fig)

def create_seasonal_chart(seasonal_pattern):
    """Bar chart showing seasonality"""
    fig = px.bar(
        seasonal_pattern, 
        x='month_name', 
        y='bio_age_5_17',
        title="Average Updates by Calendar Month (Seasonality)",
        labels={'bio_age_5_17': 'Avg Updates', 'month_name': 'Month'},
        color='bio_age_5_17',
        color_continuous_scale='Viridis'
    )
    return set_dark_theme(fig)

def create_forecast_chart(forecast_df):
    """Bar chart of predicted future gaps"""
    top_10 = forecast_df.head(10)
    fig = px.bar(
        top_10,
        x='pincode',
        y='predicted_future_gap',
        error_y='conf_high', # Simplified error bar representation
        title="Top 10 Predicted Future Gap Areas (3-Year Forecast)",
        labels={'predicted_future_gap': 'Predicted Gap', 'pincode': 'PIN Code'},
        color='forecast_risk_level',
        color_discrete_map=RISK_COLORS
    )
    return set_dark_theme(fig)

def create_risk_distribution_pie(df):
    """Pie chart of risk levels"""
    risk_counts = df['risk_level'].value_counts().reset_index()
    risk_counts.columns = ['Risk Level', 'Count']
    fig = px.pie(
        risk_counts, 
        values='Count', 
        names='Risk Level',
        color='Risk Level',
        color_discrete_map=RISK_COLORS,
        title="Distribution of Risk Levels Across PIN Codes"
    )
    return set_dark_theme(fig)

def create_risk_sunburst(df):
    """Hierarchical view of State > District > Risk Level"""
    # Note: State is added as a placeholder if not present, assuming 'Delhi' for existing data
    if 'state' not in df.columns:
        df['state'] = 'Selected Region'
        
    fig = px.sunburst(
        df, 
        path=['state', 'district', 'risk_level'], 
        values='update_gap',
        color='risk_level',
        color_discrete_map=RISK_COLORS,
        title="Hierarchical Risk Distribution (Area = Gap Size)",
        hover_data=['update_rate']
    )
    return set_dark_theme(fig)

def create_gap_treemap(df):
    """TreeMap of update gaps organized by District and Risk"""
    fig = px.treemap(
        df, 
        path=[px.Constant("All India"), 'district', 'risk_level', 'pincode'], 
        values='update_gap',
        color='priority_score',
        color_continuous_scale='Reds',
        title="Biometric Update Gap TreeMap (Weighted by Priority Score)",
        hover_data=['update_rate']
    )
    fig.update_traces(textinfo="label+value")
    return set_dark_theme(fig)

def create_performance_matrix(df):
    """Scatter matrix identifying performance quadrants"""
    # Calculate medians for quadrants
    median_gap = df['update_gap'].median()
    median_rate = df['update_rate'].median()
    
    fig = px.scatter(
        df,
        x='update_rate',
        y='update_gap',
        color='risk_level',
        color_discrete_map=RISK_COLORS,
        size='age_0_5', # Size by base population
        hover_data=['pincode', 'district'],
        title="District Performance Matrix (Gap vs. Rate)",
        labels={'update_rate': 'Update Rate (%)', 'update_gap': 'Biometric Update Gap'},
        text='pincode' # Show text labels for outliers
    )
    
    # Add quadrant lines
    fig.add_hline(y=median_gap, line_dash="dash", line_color="gray", annotation_text="High Volume Threshold")
    fig.add_vline(x=median_rate, line_dash="dash", line_color="gray", annotation_text="Efficiency Median")
    
    # Add quadrant annotations
    fig.add_annotation(x=median_rate*0.5, y=median_gap*1.5, text="High Risk / High Volume", showarrow=False, font=dict(color="red"))
    fig.add_annotation(x=median_rate*1.5, y=median_gap*0.5, text="High Efficiency / Low Gap", showarrow=False, font=dict(color="green"))
    
    return set_dark_theme(fig)

def create_bio_demo_scatter(integrated_df):
    """Scatter plot of bio vs demo updates"""
    fig = px.scatter(
        integrated_df,
        x='bio_age_5_17',
        y='demo_age_5_17',
        color='district',
        hover_data=['pincode'],
        title="Correlation: Biometric vs Demographic Updates",
        labels={'bio_age_5_17': 'Biometric Updates', 'demo_age_5_17': 'Demographic Updates'}
    )
    # Add identity line
    max_val = max(integrated_df['bio_age_5_17'].max(), integrated_df['demo_age_5_17'].max())
    fig.add_shape(
        type="line", x0=0, y0=0, x1=max_val, y1=max_val,
        line=dict(color="MediumPurple", width=2, dash="dash")
    )
    return set_dark_theme(fig)

def create_geographic_map_markers(df):
    """Creates a Folium map with markers. Uses Pincode lookup with District fallback."""
    import random
    
    # Center map on India
    m = folium.Map(location=[22.9734, 78.6569], zoom_start=5, tiles='CartoDB positron')
    
    # Pincode coordinates (selective)
    pincode_coords = {
        '110001': [28.6315, 77.2167], '110002': [28.6441, 77.2346],
        '110003': [28.5983, 77.2312], '110004': [28.6139, 77.2090],
        '110005': [28.6531, 77.1904], '110006': [28.6601, 77.2311],
        '110007': [28.6801, 77.2032], '110008': [28.6453, 77.1587]
    }
    
    # District Level Fallback Coords
    district_coords = {
        'Central Delhi': [28.6441, 77.2346], 'West Delhi': [28.6675, 77.0706],
        'North East Delhi': [28.6914, 77.2692], 'South West Delhi': [28.5733, 77.0105],
        'Hyderabad': [17.3850, 78.4867], 'Adilabad': [19.6641, 78.5320],
        'Chandigarh': [30.7333, 76.7794], 'Darbhanga': [26.1167, 85.8917],
        'Gadchiroli': [20.1000, 79.9833], 'Gaya': [24.7914, 85.0002],
        'Khammam': [17.2473, 80.1514], 'Kishanganj': [26.0717, 87.9383],
        'Mohali': [30.7046, 76.7179], 'Mumbai Suburban': [19.1264, 72.8567],
        'Muzaffarpur': [26.1209, 85.3647], 'Nizamabad': [18.6725, 78.0941],
        'Patna': [25.5941, 85.1376], 'Pune': [18.5204, 73.8567],
        'Purnia': [25.7771, 87.4753], 'Rangareddy': [17.3700, 78.4800],
        'Warangal': [17.9784, 79.5941]
    }
    
    for _, row in df.iterrows():
        pincode = str(row['pincode'])
        district = str(row['district'])
        loc = None
        
        if pincode in pincode_coords:
            loc = pincode_coords[pincode]
        elif district in district_coords:
            # Fallback to district with a small jitter to avoid perfect overlap
            base_loc = district_coords[district]
            loc = [base_loc[0] + random.uniform(-0.05, 0.05), 
                   base_loc[1] + random.uniform(-0.05, 0.05)]
        
        if loc:
            color = RISK_COLORS.get(row['risk_level'], 'gray')
            folium.CircleMarker(
                location=loc,
                radius=min(25, 5 + (row['update_gap'] / 200)), # Scaled radius
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.6,
                popup=(f"<b>PIN: {pincode}</b><br>District: {district}<br>"
                       f"Gap: {row['update_gap']:,}<br>"
                       f"Rate: {row['update_rate']:.1f}%<br>Risk: {row['risk_level']}")
            ).add_to(m)
            
    return m
