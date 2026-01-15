import vertexai
from vertexai.generative_models import GenerativeModel
import google.auth
from google.oauth2 import service_account
import os
import json
from dotenv import load_dotenv

load_dotenv()

class GeminiAnalyzer:
    _insight_cache = {} # Class-level cache for hover insights
    
    def __init__(self):
        project_id = os.environ.get("GOOGLE_CLOUD_PROJECT") or os.environ.get("PROJECT_ID")
        location = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
        key_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
        
        # Try to find service account in root if key_path not set
        if not key_path or not os.path.exists(key_path):
            root_sa = os.path.join(os.getcwd(), 'service-account.json')
            if os.path.exists(root_sa):
                key_path = root_sa

        self.error_reason = None
        
        # Priority 1: Service Account JSON (Bypasses all plugin errors)
        if key_path and os.path.exists(key_path) and key_path.endswith('.json'):
            try:
                # EXPLICITLY load credentials to bypass gcloud plugin discovery
                creds = service_account.Credentials.from_service_account_file(key_path)
                
                # Auto-detect project ID from service account if missing
                if not project_id:
                    project_id = creds.project_id
                
                vertexai.init(project=project_id, location=location, credentials=creds)
                self.model = GenerativeModel("gemini-2.5-flash")
                self.enabled = True
                print(f"AI Enabled: Project={project_id}, Location={location}")
                return
            except Exception as e:
                self.error_reason = f"SA Auth: {str(e)}"
                print(f"Service Account Auth Error: {str(e)}")

        # Priority 2: Standard ADC (May trigger plugin error on Windows)
        if project_id:
            os.environ["GOOGLE_CLOUD_QUOTA_PROJECT"] = project_id
            try:
                vertexai.init(project=project_id, location=location)
                self.model = GenerativeModel("gemini-2.5-flash")
                self.enabled = True
                print(f"AI Enabled (ADC): Project={project_id}, Location={location}")
            except Exception as e:
                self.error_reason = f"ADC Auth: {str(e)}"
                print(f"Auth Error: {str(e)}")
                self.enabled = False
        else:
            self.error_reason = "No Project ID provided in environment or service account."
            self.enabled = False

    def generate_narrative_insights(self, dashboard_data):
        """
        Synthesizes dashboard data into a professional advisory report.
        """
        if not self.enabled:
            return f"⚠️ AI Feature Inactive: {self.error_reason or 'Configuration error'}. Please verify GOOGLE_CLOUD_PROJECT or service-account.json."

        # Prepare summary for Gemini
        summary = {
            "total_gap": dashboard_data.get('total_gap'),
            "critical_pins": dashboard_data.get('critical_pins'),
            "update_rate": f"{dashboard_data.get('update_rate', 0):.1f}%",
            "forecasted_gap": dashboard_data.get('forecasted_gap'),
            "top_districts": dashboard_data.get('top_districts'),
            "anomalies": dashboard_data.get('anomalies'),
            "vans_needed": dashboard_data.get('vans_needed'),
            "system_baselines": dashboard_data.get('system_baselines', {}),
            "regional_benchmarks": dashboard_data.get('regional_benchmarks', {})
        }

        prompt = f"""
        You are 'UIDAI-Optimus', a strategic AI advisor for the Unique Identification Authority of India.
        Based on the following data regarding the 'Forgotten Children' (children who missed mandatory biometric updates), 
        provide a concise, high-level strategic advisory report.

        DATA SUMMARY:
        {json.dumps(summary, indent=2)}

        YOUR REPORT SHOULD INCLUDE:
        1. **Executive Summary**: 2 sentences on the systemic state of Aadhaar coverage.
        2. **Cross-Dataset Synthesis**: Analyze how update rates correlate with enrollment baselines and demographic signals.
        3. **Critical Risk Zones**: Identify districts where inclusion risk is highest or update infrastructure is lagging.
        4. **Tactical Recommendation**: Specifically mention mobile van deployment and localized strategies.
        5. **Prediction Insight**: Commentary on the forecasted gap vs the current system capacity.

        Format with professional Markdown. Use a tone that is authoritative yet helpful.
        """

        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"❌ Error generating AI insights: {str(e)}"

    def generate_point_insight(self, context, hover_data, global_context=None):
        """
        Generates a quick, dynamic explanation for a specific data point on hover.
        Utilizes a class-level cache to prevent redundant API calls.
        """
        if not self.enabled:
            return "AI Insight Unavailable"

        # Unique key for caching based on context, hover data, and a hash of global context if provided
        cache_key = f"{context}_{str(hover_data)}"
        if cache_key in self._insight_cache:
            return self._insight_cache[cache_key]

        # Structure the global context for the prompt
        context_str = ""
        if global_context:
            context_str = f"GLOBAL SYSTEM CONTEXT:\n{json.dumps(global_context, indent=2)}\n"

        prompt = f"""
        You are 'UIDAI-Optimus', a strategic AI advisor for UIDAI.
        Provide a 2-sentence tactical explanation for this specific data point.
        
        {context_str}
        
        POINT CONTEXT: {context}
        HOVERED DATA: {json.dumps(hover_data)}

        YOUR TASK:
        1. Explain what this data point represents in the context of the 'Forgotten Children' system.
        2. IF GLOBAL CONTEXT IS PROVIDED: Compare this point to the national/regional averages or forecasts (e.g. 'This is 15% lower than the state benchmark').
        3. Identify the immediate tactical action (e.g. 'Deploy mobile van', 'Conduct awareness drive').

        Keep it brief, professional, and data-driven. Use **bold text** for key metrics or actions.
        """

        try:
            response = self.model.generate_content(prompt)
            result = response.text
            self._insight_cache[cache_key] = result # Store in cache
            return result
        except Exception as e:
            error_msg = str(e)
            print(f"AI Point Insight Error: {error_msg}")
            if "429" in error_msg:
                return "💡 AI is *cooling down* due to high hover activity. Please pause for a moment."
            return f"❌ AI Error: {error_msg[:100]}..." # Show brief error in UI for debugging

    @staticmethod
    def extract_summary_for_ai(priority_df, forecast_df, anomaly_df, enroll_df=None, bio_df=None, demo_df=None):
        """Helper to prepare the data packet with multi-dataset context"""
        top_dists = priority_df.groupby('district')['update_gap'].sum().nlargest(3).to_dict()
        anomaly_summary = anomaly_df['anomaly_type'].value_counts().to_dict() if not anomaly_df.empty else {}
        
        # Calculate cross-dataset metrics if raw data provided
        system_stats = {}
        if enroll_df is not None and not enroll_df.empty:
            system_stats['total_eligible_base'] = int(enroll_df['age_0_5'].sum() + enroll_df['age_5_17'].sum())
            system_stats['enrollment_coverage_districts'] = int(enroll_df['district'].nunique())
            
        if bio_df is not None and not bio_df.empty:
            system_stats['cumulative_biometric_updates'] = int(bio_df['bio_age_5_17'].sum() + bio_df['bio_age_17_'].sum())
            
        if demo_df is not None and not demo_df.empty:
            system_stats['demographic_mobility_signal'] = int(demo_df['demo_age_5_17'].sum())
            
        # Regional Maturity index (heuristic)
        regional_maturity = {}
        if 'update_rate' in priority_df.columns:
            top_performing = priority_df.nlargest(3, 'update_rate')[['district', 'update_rate']].to_dict('records')
            bottom_performing = priority_df.nsmallest(3, 'update_rate')[['district', 'update_rate']].to_dict('records')
            regional_maturity = {
                "efficiency_leaders": top_performing,
                "inclusion_risk_zones": bottom_performing
            }

        return {
            "total_gap": int(priority_df['update_gap'].sum()),
            "critical_pins": int((priority_df['risk_level'] == 'Critical').sum()),
            "update_rate": float(priority_df['update_rate'].mean()),
            "forecasted_gap": int(forecast_df['predicted_future_gap'].sum()),
            "top_districts": top_dists,
            "anomalies": anomaly_summary,
            "vans_needed": int(priority_df['estimated_vans_needed'].sum()),
            "system_baselines": system_stats,
            "regional_benchmarks": regional_maturity
        }
