import json
import google.generativeai as genai
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class InsightEngine:
    def __init__(self, api_key=None):
        # Use provided API key or load from environment
        if api_key:
            genai.configure(api_key=api_key)
        else:
            api_key = os.getenv('GEMINI_API_KEY')
            if api_key:
                genai.configure(api_key=api_key)
            else:
                raise ValueError("GEMINI_API_KEY not found. Please set it in .env file or pass it as argument.")
        
        self.model = genai.GenerativeModel('gemini-2.5-flash')

    def structure_insight(self, category, district, metrics, timeframe):
        """Converts raw analytics into a structured insight object."""
        insight = {
            "type": "societal_intelligence",
            "category": category,
            "geography": district,
            "time_range": timeframe,
            "metrics": metrics,
            "confidence_score": 0.85 # Placeholder for statistical confidence
        }
        return insight

    def explain_with_gemini(self, insight_object):
        """Uses Gemini to generate human-readable explanations based on structured insights."""
        prompt = f"""
        You are an expert socio-economic analyst specializing in Aadhaar (UIDAI) data.
        Analyze the following structured insight and explain:
        1. WHAT is happening in this district?
        2. WHY might this be happening (potential societal drivers like migration, labor, etc.)?
        3. WHAT NEXT? (Recommendations for policymakers).

        Keep the explanation professional, concise, and actionable.
        DO NOT invent raw numbers. Use only the provided metrics.

        INSIGHT DATA:
        {json.dumps(insight_object, indent=2)}

        OUTPUT FORMAT:
        Summary: [Brief summary]
        Analysis: [What and Why]
        Recommendations: [Action points]
        """
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Error generating explanation: {str(e)}"

if __name__ == "__main__":
    # Example usage (Mock metrics)
    engine = InsightEngine() # Assuming OS environment variable GEMINI_API_KEY is set or handled by the platform
    mock_metrics = {
        "adult_enrolment_ratio": 0.15,
        "biometric_stress_index": 2.1,
        "migration_intensity_index": 1.5
    }
    insight = engine.structure_insight("Inclusion & Mobility", "Hyderabad", mock_metrics, "2025-03 to 2026-01")
    print("Structured Insight:")
    print(json.dumps(insight, indent=2))
    
    # print("\nGemini Explanation:")
    print(engine.explain_with_gemini(insight))
