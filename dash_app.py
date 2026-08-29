import dash
from dash import dcc, html, dash_table, Input, Output, State
import dash_bootstrap_components as dbc
import pandas as pd
import os
import sys
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.getcwd(), 'src'))

from src.data_loader import UIDAIDataLoader
from src.data_integrator import DataIntegrator
from src.analytics.gap_calculator import GapCalculator
from src.analytics.priority_scorer import PriorityScorer
from src.analytics.temporal_analyzer import TemporalAnalyzer
from src.analytics.forecasting import ForecastingEngine
from src.analytics.anomaly_detector import AnomalyDetector
from src.analytics.report_generator import ReportGenerator
from src.analytics.ai_analyzer import AIAnalyzer
import src.visualizations as viz

# Global AI Analyzer instance
_analyzer = None

def get_analyzer():
    global _analyzer
    if _analyzer is None:
        _analyzer = AIAnalyzer()
    return _analyzer

# Initialize Dash App
app = dash.Dash(
    __name__, 
    external_stylesheets=[dbc.themes.BOOTSTRAP, 'https://fonts.googleapis.com/css2?family=Open+Sans:wght@300;400;600;700&display=swap'],
    suppress_callback_exceptions=True,
    assets_folder='assets',
    serve_locally=True
)
app.title = "Forgotten Children - UIDAI Professional Analytics"

# Data Loading Engine
def load_all_data():
    loader = UIDAIDataLoader(os.getcwd())
    enrollment = loader.load_dataset('enrollment')
    biometric = loader.load_dataset('biometric')
    demographic = loader.load_dataset('demographic')
    
    integrated = DataIntegrator.integrate(enrollment, biometric, demographic)
    
    gap_df = GapCalculator.calculate_gaps(integrated)
    gap_df = GapCalculator.calculate_detailed_metrics(gap_df)
    
    scorer = PriorityScorer()
    priority_df = scorer.calculate_priority_scores(gap_df)
    priority_df = scorer.model_intervention_resources(priority_df)
    
    forecast_df = ForecastingEngine.forecast_future_gaps(enrollment, gap_df)
    anomaly_df = AnomalyDetector.detect_anomalies(gap_df)
    
    # Temporal Trends
    monthly_trend, seasonal_pattern, temporal_insights = TemporalAnalyzer.analyze_trends(biometric)
    
    ai_prompt_instructions = """
        YOUR REPORT SHOULD INCLUDE:
        1. **Executive Summary**: 2 sentences on the systemic state of children's Aadhaar inclusion.
        2. **Cross-Dataset Synthesis**: Analyze how regional update rates correlate with enrollment baselines and demographic signals.
        3. **Critical Risk Zones**: Identify districts where the gap is widening despite capacity or where update infrastructure is lagging.
        4. **Tactical Recommendation**: Specifically mention mobile van deployment and localized awareness strategies.
        5. **Prediction Insight**: Commentary on the forecasted gap vs the existing update trajectory.

        Format with professional Markdown. Use a tone that is authoritative yet helpful.
        """
    
    return {
        'enrollment': enrollment, # Added
        'biometric': biometric,
        'demographic': demographic, # Added
        'integrated': integrated,
        'gap_df': gap_df, # Added
        'priority_df': priority_df,
        'forecast_df': forecast_df,
        'anomaly_df': anomaly_df,
        'monthly_trend': monthly_trend,
        'seasonal_pattern': seasonal_pattern,
        'temporal_insights': temporal_insights,
        'ai_prompt_instructions': ai_prompt_instructions # Added
    }

# UI Component: KPI Card
def make_kpi_card(title, value, color_class):
    return dbc.Card([
        dbc.CardBody([
            html.Div(title, className="kpi-title"),
            html.Div(value, className=f"kpi-value {color_class}"),
        ])
    ])

# App Layout
app.layout = dbc.Container([
    # Store data
    dcc.Store(id='full-data-store'),
    dcc.Store(id='ai-context-store'),

    # Header
    dbc.Row([
        dbc.Col([
            html.H2("🛡️ THE FORGOTTEN CHILDREN", className="section-title mt-4"),
            html.P("Biometric Update Gap Analysis | UIDAI Professional Intelligence", className="text-muted"),
        ], width=8),
        dbc.Col([
            dbc.Button("🔄 REFRESH DATA", id="refresh-btn", color="primary", className="mt-4 float-end"),
        ], width=4)
    ], className="mb-4"),


    # KPI Row
    dbc.Row(id='kpi-row', className="mb-4"),

    # Tactical Intelligence Row (Detailed metrics)
    dbc.Row([
        dbc.Col(id='urgency-kpi-container', width=3),
        dbc.Col(id='saturation-kpi-container', width=3),
        dbc.Col(id='van-resource-kpi-container', width=6),
    ], className="mb-4"),

    # Main Grid (Map & Priority Table)
    dbc.Row([ 
        dbc.Col([
            dbc.Card([
                html.H5("Geographic Risk Distribution", className="mb-3 font-weight-light"),
                html.Div([
                    dcc.Graph(id='mapbox-geo', config={'displayModeBar': False}),
                    html.Div(id='ai-map-overlay', className="ai-hover-overlay")
                ], style={'position': 'relative'}),
                html.Div(id='district-scorecard', className="mt-3")
            ])
        ], width=8),
        dbc.Col([
            dbc.Card([
                html.H5("Priority Action List", className="mb-3 font-weight-light"),
                html.Div(id='priority-table-container')
            ], style={'height': '540px', 'overflowY': 'auto'})
        ], width=4)
    ], className="mb-4"),

    # Analytics Row
    dbc.Row([
        dbc.Col([
            dbc.Card([
                html.H5("Temporal Update Trends", className="mb-3"),
                html.Div([
                    dcc.Graph(id='trend-chart'),
                    html.Div(id='ai-trend-overlay', className="ai-hover-overlay")
                ], style={'position': 'relative'})
            ])
        ], width=6),
        dbc.Col([
            dbc.Card([
                html.H5("Risk Hierarchy (State > District)", className="mb-3"),
                html.Div([
                    dcc.Graph(id='sunburst-chart'),
                    html.Div(id='ai-sunburst-overlay', className="ai-hover-overlay")
                ], style={'position': 'relative'})
            ])
        ], width=6),
    ], className="mb-4"),

    # Bottom Row
    dbc.Row([
        dbc.Col([
            dbc.Card([
                html.H5("⚠️ Anomaly Detection Feed", className="mb-3 text-neon-orange"),
                html.Div(id='anomaly-list', className="anomaly-feed")
            ])
        ], width=6),
        dbc.Col([
            dbc.Card([
                html.H5("District Performance Matrix", className="mb-3"),
                html.Div([
                    dcc.Graph(id='matrix-chart'),
                    html.Div(id='ai-matrix-overlay', className="ai-hover-overlay")
                ], style={'position': 'relative'})
            ])
        ], width=6)
    ], className="mb-4"),

    # New Detailed Analytics Row
    dbc.Row([
        dbc.Col([
            dbc.Card([
                html.H5("Gap Hierarchy TreeMap (District > Risk)", className="mb-3"),
                html.Div([
                    dcc.Graph(id='treemap-chart'),
                    html.Div(id='ai-treemap-overlay', className="ai-hover-overlay")
                ], style={'position': 'relative'})
            ])
        ], width=12),
    ])
], fluid=True, className="dashboard-container")

# Callbacks
@app.callback(
    Output('full-data-store', 'data'),
    Input('refresh-btn', 'n_clicks'),
)
def update_data(n):
    data = load_all_data()
    # Convert dataframes to dicts for storage
    return {k: v.to_dict('records') if hasattr(v, 'to_dict') else v for k, v in data.items()}

@app.callback(
    [Output('kpi-row', 'children'),
     Output('urgency-kpi-container', 'children'),
     Output('saturation-kpi-container', 'children'),
     Output('van-resource-kpi-container', 'children'),
     Output('mapbox-geo', 'figure'),
     Output('priority-table-container', 'children'),
     Output('trend-chart', 'figure'),
     Output('sunburst-chart', 'figure'),
     Output('matrix-chart', 'figure'),
     Output('treemap-chart', 'figure'),
     Output('anomaly-list', 'children'),
     Output('ai-context-store', 'data')],
    Input('full-data-store', 'data')
)
def populate_dashboard(data):
    if not data:
        return dash.no_update
    
    # Restore Dataframes
    priority_df = pd.DataFrame(data['priority_df'])
    monthly_trend = pd.DataFrame(data['monthly_trend'])
    forecast_df = pd.DataFrame(data['forecast_df'])
    anomaly_df = pd.DataFrame(data['anomaly_df'])
    integrated = pd.DataFrame(data['integrated'])
    enroll_df = pd.DataFrame(data['enrollment'])
    bio_df = pd.DataFrame(data['biometric'])
    demo_df = pd.DataFrame(data['demographic'])
    
    # Generate Global AI Context for smart hovering
    ai_context = AIAnalyzer.extract_summary_for_ai(
        priority_df, forecast_df, anomaly_df,
        enroll_df=enroll_df, bio_df=bio_df, demo_df=demo_df
    )
    
    # 1. Primary KPIs
    stats = GapCalculator.get_summary_stats(priority_df)
    kpis = [
        dbc.Col(make_kpi_card("Baseline Gap (Children)", f"{stats['total_at_risk']:,}", "metric-neon-pink"), width=3),
        dbc.Col(make_kpi_card("Critical Interventions", stats['critical_pins'], "metric-neon-orange"), width=3),
        dbc.Col(make_kpi_card("System Efficiency", f"{stats['overall_update_rate']:.1f}%", "metric-neon-green"), width=3),
        dbc.Col(make_kpi_card("Horizon Risk", f"{int(forecast_df['predicted_future_gap'].sum()):,}", "metric-neon-blue"), width=3),
    ]

    # 2. Detailed Intelligence Rows
    urgency_kpi = make_kpi_card("Avg Urgency Index", f"{priority_df['urgency_index'].mean():.1f}", "metric-neon-orange")
    saturation_kpi = make_kpi_card("User Awareness Index", f"{priority_df['saturation_index'].mean():.1f}%", "metric-neon-green")
    van_kpi = make_kpi_card("Total Mobile Unit Capital (Est.)", f"{int(priority_df['estimated_vans_needed'].sum())} Aadhaar Vans", "metric-neon-blue")
    
    # 3. Map
    map_fig = viz.create_geographic_mapbox(priority_df)
    
    # 3. Priority Table
    top_list = ReportGenerator.get_priority_list(priority_df, top_n=10)
    table = dash_table.DataTable(
        data=top_list.to_dict('records'),
        columns=[{"name": i.replace('_', ' ').title(), "id": i} for i in top_list.columns],
        style_table={'overflowX': 'auto'},
        style_as_list_view=True,
        style_header={
            'backgroundColor': 'rgba(0,0,0,0)',
            'color': '#9a9a9a',
            'borderBottom': '1px solid #2b2d42',
            'textAlign': 'left',
            'fontWeight': '600'
        },
        style_cell={
            'backgroundColor': 'rgba(0,0,0,0)',
            'color': '#ffffff',
            'border': 'none',
            'padding': '12px',
            'textAlign': 'left',
            'fontSize': '0.85rem'
        },
        style_data_conditional=[
            {
                'if': {'column_id': 'risk_level', 'filter_query': '{risk_level} eq "Critical"'},
                'color': '#ff5252'
            },
            {
                'if': {'column_id': 'risk_level', 'filter_query': '{risk_level} eq "High"'},
                'color': '#ffab40'
            }
        ]
    )
    
    # 4. Charts
    trend_fig = viz.create_temporal_line_chart(monthly_trend)
    sunburst_fig = viz.create_risk_sunburst(priority_df)
    matrix_fig = viz.create_performance_matrix(priority_df)
    treemap_fig = viz.create_gap_treemap(priority_df)
    
    # 5. Anomalies
    if not anomaly_df.empty:
        anomalies = html.Div([
            html.Div([
                html.Span(row['anomaly_type'], className=f"risk-badge {('risk-critical' if row['severity']=='Critical' else 'risk-high')} mr-2"),
                html.Span(f" - {row['pincode']} ({row['district']})", className="ml-2"),
                html.P(row['description'], className="small text-muted mb-3")
            ]) for _, row in anomaly_df.head(5).iterrows()
        ])
    else:
        anomalies = html.P("No anomalies detected.", className="text-muted")
        
    return kpis, urgency_kpi, saturation_kpi, van_kpi, map_fig, table, trend_fig, sunburst_fig, matrix_fig, treemap_fig, anomalies, ai_context

@app.callback(
    Output('district-scorecard', 'children'),
    [Input('mapbox-geo', 'clickData')],
    [State('full-data-store', 'data')]
)
def display_district_details(clickData, data):
    if not clickData or not data:
        return html.Div("Click a point on the map to see tactical details.", className="text-muted small italic")
    
    pincode = clickData['points'][0]['hovertext']
    priority_df = pd.DataFrame(data['priority_df'])
    forecast_df = pd.DataFrame(data['forecast_df'])
    
    district_data = priority_df[priority_df['pincode'].astype(str) == str(pincode)].iloc[0]
    
    # Get regional forecast if available
    region_forecast = forecast_df[forecast_df['pincode'].astype(str) == str(pincode)]
    forecast_text = f"{int(region_forecast['predicted_future_gap'].iloc[0]):,}" if not region_forecast.empty else "N/A"
    
    return dbc.Card([
        dbc.CardBody([
            html.H6(f"Tactical Scorecard: PIN {pincode}", className="text-neon-blue mb-3"),
            dbc.Row([
                dbc.Col([
                    html.P("Efficiency vs State", className="small text-muted mb-0"),
                    html.H5(f"{district_data['vs_state_avg']:+.1f}%", 
                           className=f"{'text-success' if district_data['vs_state_avg'] > 0 else 'text-danger'}")
                ], width=3),
                dbc.Col([
                    html.P("Awareness Index", className="small text-muted mb-0"),
                    html.H5(f"{district_data['saturation_index']:.1f}%", className="text-white")
                ], width=3),
                dbc.Col([
                    html.P("Vans Required", className="small text-muted mb-0"),
                    html.H5(f"{district_data['estimated_vans_needed']}", className="text-warning")
                ], width=3),
                dbc.Col([
                    html.P("Forecasted Gap", className="small text-muted mb-0"),
                    html.H5(forecast_text, className="text-neon-pink")
                ], width=3),
            ]),
            html.Hr(className="bg-secondary"),
            html.P([
                html.B("Recommendation: "),
                district_data['recommended_action']
            ], className="small text-white mb-0")
        ])
    ])


# --- DYNAMIC AI HOVER CALLBACKS ---

@app.callback(
    [Output('ai-map-overlay', 'children'),
     Output('ai-map-overlay', 'style')],
    [Input('mapbox-geo', 'hoverData')],
    [State('ai-context-store', 'data')],
    prevent_initial_call=True
)
def update_map_ai_insight(hoverData, global_context):
    if not hoverData:
        return "", {'display': 'none'}
    
    try:
        analyzer = get_analyzer()
        point_data = hoverData['points'][0]
        insight = analyzer.generate_point_insight("Geographic Risk Point", point_data['hovertext'], global_context=global_context)
        
        return dcc.Markdown(insight), {
            'display': 'block',
            'top': '10px',
            'right': '10px'
        }
    except Exception as e:
        print(f"Callback Error (Map): {e}")
        return dash.no_update

@app.callback(
    [Output('ai-trend-overlay', 'children'),
     Output('ai-trend-overlay', 'style')],
    [Input('trend-chart', 'hoverData')],
    [State('ai-context-store', 'data')],
    prevent_initial_call=True
)
def update_trend_ai_insight(hoverData, global_context):
    if not hoverData:
        return "", {'display': 'none'}
    
    try:
        analyzer = get_analyzer()
        point_data = hoverData['points'][0]
        insight = analyzer.generate_point_insight("Temporal Trend Node", {"Date": point_data['x'], "Value": point_data['y']}, global_context=global_context)
        
        return dcc.Markdown(insight), {
            'display': 'block',
            'top': '10px',
            'right': '10px'
        }
    except Exception as e:
        print(f"Callback Error (Trend): {e}")
        return dash.no_update

@app.callback(
    [Output('ai-sunburst-overlay', 'children'),
     Output('ai-sunburst-overlay', 'style')],
    [Input('sunburst-chart', 'hoverData')],
    [State('ai-context-store', 'data')],
    prevent_initial_call=True
)
def update_sunburst_ai_insight(hoverData, global_context):
    if not hoverData:
        return "", {'display': 'none'}
    
    try:
        analyzer = get_analyzer()
        point_data = hoverData['points'][0]
        insight = analyzer.generate_point_insight("Hierarchical Risk Segment", point_data['label'], global_context=global_context)
        
        return dcc.Markdown(insight), {
            'display': 'block',
            'top': '10px',
            'right': '10px'
        }
    except Exception as e:
        print(f"Callback Error (Sunburst): {e}")
        return dash.no_update

@app.callback(
    [Output('ai-matrix-overlay', 'children'),
     Output('ai-matrix-overlay', 'style')],
    [Input('matrix-chart', 'hoverData')],
    [State('ai-context-store', 'data')],
    prevent_initial_call=True
)
def update_matrix_ai_insight(hoverData, global_context):
    if not hoverData:
        return "", {'display': 'none'}
    
    try:
        analyzer = get_analyzer()
        point_data = hoverData['points'][0]
        insight = analyzer.generate_point_insight("District Performance Metric", {"District": point_data['hovertext'], "Gap": point_data['y'], "Rate": point_data['x']}, global_context=global_context)
        
        return dcc.Markdown(insight), {
            'display': 'block',
            'top': '10px',
            'right': '10px'
        }
    except Exception as e:
        print(f"Callback Error (Matrix): {e}")
        return dash.no_update

@app.callback(
    [Output('ai-treemap-overlay', 'children'),
     Output('ai-treemap-overlay', 'style')],
    [Input('treemap-chart', 'hoverData')],
    [State('ai-context-store', 'data')],
    prevent_initial_call=True
)
def update_treemap_ai_insight(hoverData, global_context):
    if not hoverData:
        return "", {'display': 'none'}
    
    try:
        analyzer = get_analyzer()
        point_data = hoverData['points'][0]
        insight = analyzer.generate_point_insight("Hierarchical TreeMap Node", point_data['label'], global_context=global_context)
        
        return dcc.Markdown(insight), {
            'display': 'block',
            'top': '10px',
            'right': '10px'
        }
    except Exception as e:
        print(f"Callback Error (TreeMap): {e}")
        return dash.no_update

if __name__ == '__main__':
    app.run(debug=True, port=8050)
