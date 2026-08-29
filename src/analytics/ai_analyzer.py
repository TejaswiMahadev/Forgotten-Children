"""OpenRouter-backed narrative layer for the dashboard.

Replaces the previous Vertex AI / Gemini integration. OpenRouter exposes an
OpenAI-compatible chat-completions endpoint, so this needs no SDK -- the stdlib
is enough, which keeps another unpinned package out of requirements.txt.

Configuration (all via .env, never hardcoded):
    OPENROUTER_API_KEY   required to enable the AI layer
    OPENROUTER_MODEL     optional, defaults to DEFAULT_MODEL below
"""

import json
import os
import urllib.error
import urllib.request

from dotenv import load_dotenv

load_dotenv()

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# Free-tier default. Verified to answer the point-insight prompt in ~4s without
# leaking a reasoning trace into the output (several other free models do).
DEFAULT_MODEL = "minimax/minimax-m3:free"

# This call happens inside a Dash callback, on the request thread. Without a
# timeout a hung provider hangs the worker and the dashboard stops responding.
REQUEST_TIMEOUT = 30

# Blunt backstop, not a substitute for fixing the real problem: every chart
# hover triggers a call (finding F9 in PROJECT_GUIDE.md), and OpenRouter's free
# tier allows only a few dozen requests a day. Without this, one mouse sweep
# across the treemap exhausts the daily quota.
MAX_CALLS_PER_PROCESS = 40


class AIAnalyzer:
    """Generates narrative and per-point insights via OpenRouter."""

    _insight_cache = {}   # class-level, shared across instances
    _calls_made = 0

    def __init__(self, api_key=None, model=None):
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY")
        self.model = model or os.environ.get("OPENROUTER_MODEL", DEFAULT_MODEL)
        self.error_reason = None
        self.enabled = bool(self.api_key)

        if self.enabled:
            print(f"AI enabled: OpenRouter, model={self.model}")
        else:
            self.error_reason = "OPENROUTER_API_KEY is not set -- add it to .env"
            print(f"AI disabled: {self.error_reason}")

    @classmethod
    def calls_remaining(cls):
        return max(0, MAX_CALLS_PER_PROCESS - cls._calls_made)

    def _chat(self, prompt, max_tokens=800):
        """One chat-completion round trip. Returns (text, error_message)."""
        cls = type(self)
        if cls._calls_made >= MAX_CALLS_PER_PROCESS:
            return None, (
                f"per-session budget of {MAX_CALLS_PER_PROCESS} AI calls is spent"
            )
        cls._calls_made += 1

        body = json.dumps({
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
        }).encode("utf-8")

        request = urllib.request.Request(
            OPENROUTER_URL,
            data=body,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                # Optional OpenRouter attribution headers.
                "X-Title": "Forgotten Children of Aadhaar",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT) as response:
                payload = json.loads(response.read().decode("utf-8"))
            return payload["choices"][0]["message"]["content"].strip(), None
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", "replace")[:200]
            return None, f"HTTP {exc.code}: {detail}"
        except (KeyError, IndexError, ValueError) as exc:
            return None, f"Unexpected response shape: {type(exc).__name__}: {exc}"
        except Exception as exc:
            return None, f"{type(exc).__name__}: {exc}"

    def generate_narrative_insights(self, dashboard_data):
        """Synthesizes dashboard data into a professional advisory report."""
        if not self.enabled:
            return f"AI feature inactive: {self.error_reason}"

        summary = {
            "total_gap": dashboard_data.get("total_gap"),
            "critical_pins": dashboard_data.get("critical_pins"),
            "update_rate": f"{dashboard_data.get('update_rate', 0):.1f}%",
            "forecasted_gap": dashboard_data.get("forecasted_gap"),
            "top_districts": dashboard_data.get("top_districts"),
            "anomalies": dashboard_data.get("anomalies"),
            "vans_needed": dashboard_data.get("vans_needed"),
            "system_baselines": dashboard_data.get("system_baselines", {}),
            "regional_benchmarks": dashboard_data.get("regional_benchmarks", {}),
        }

        prompt = f"""
        You are 'UIDAI-Optimus', a strategic AI advisor for the Unique Identification Authority of India.
        Based on the following data regarding the 'Forgotten Children' (children who missed mandatory
        biometric updates), provide a concise, high-level strategic advisory report.

        DATA SUMMARY:
        {json.dumps(summary, indent=2)}

        YOUR REPORT SHOULD INCLUDE:
        1. **Executive Summary**: 2 sentences on the systemic state of Aadhaar coverage.
        2. **Cross-Dataset Synthesis**: How update rates correlate with enrollment baselines and demographic signals.
        3. **Critical Risk Zones**: Districts where inclusion risk is highest or update infrastructure is lagging.
        4. **Tactical Recommendation**: Specifically mention mobile van deployment and localized strategies.
        5. **Prediction Insight**: Commentary on the forecasted gap vs the current system capacity.

        Do not invent figures. Use only the metrics provided.
        Format with professional Markdown. Authoritative but helpful in tone.
        """

        text, error = self._chat(prompt, max_tokens=1200)
        if error:
            print(f"AI narrative error: {error}")
            return f"Could not generate AI insights -- {error}"
        return text

    def generate_point_insight(self, context, hover_data, global_context=None):
        """Short tactical explanation for one hovered data point.

        Cached per point, because hover events fire continuously as the pointer
        moves and each miss costs a real API call.
        """
        if not self.enabled:
            return "AI Insight Unavailable"

        cache_key = f"{context}_{hover_data}"
        if cache_key in self._insight_cache:
            return self._insight_cache[cache_key]

        context_block = ""
        if global_context:
            context_block = f"GLOBAL SYSTEM CONTEXT:\n{json.dumps(global_context, indent=2)}\n"

        prompt = f"""
        You are 'UIDAI-Optimus', a strategic AI advisor for UIDAI.
        Provide a 2-sentence tactical explanation for this specific data point.

        {context_block}

        POINT CONTEXT: {context}
        HOVERED DATA: {json.dumps(hover_data)}

        YOUR TASK:
        1. Explain what this data point represents in the 'Forgotten Children' system.
        2. If global context is provided, compare this point to the national or regional
           benchmark (e.g. 'this is 15% below the state benchmark').
        3. Name the immediate tactical action (e.g. deploy a mobile van, run an awareness drive).

        Answer directly with the two sentences -- no preamble and no reasoning trace.
        Keep it brief, professional and data-driven. Use **bold** for key metrics or actions.
        """

        text, error = self._chat(prompt, max_tokens=300)

        if error:
            print(f"AI point insight error: {error}")
            if "429" in error:
                return "AI is *cooling down* after heavy hover activity. Pause for a moment."
            if "budget" in error:
                return (
                    "AI call budget for this session is spent. Restart the app to reset, "
                    "or raise `MAX_CALLS_PER_PROCESS` in `ai_analyzer.py`."
                )
            return f"AI unavailable: {error[:120]}"

        self._insight_cache[cache_key] = text
        return text

    @staticmethod
    def extract_summary_for_ai(priority_df, forecast_df, anomaly_df,
                               enroll_df=None, bio_df=None, demo_df=None):
        """Prepares the data packet with multi-dataset context."""
        top_dists = priority_df.groupby('district')['update_gap'].sum().nlargest(3).to_dict()
        anomaly_summary = anomaly_df['anomaly_type'].value_counts().to_dict() if not anomaly_df.empty else {}

        system_stats = {}
        if enroll_df is not None and not enroll_df.empty:
            system_stats['total_eligible_base'] = int(enroll_df['age_0_5'].sum() + enroll_df['age_5_17'].sum())
            system_stats['enrollment_coverage_districts'] = int(enroll_df['district'].nunique())

        if bio_df is not None and not bio_df.empty:
            system_stats['cumulative_biometric_updates'] = int(bio_df['bio_age_5_17'].sum() + bio_df['bio_age_17_'].sum())

        if demo_df is not None and not demo_df.empty:
            system_stats['demographic_mobility_signal'] = int(demo_df['demo_age_5_17'].sum())

        regional_maturity = {}
        if 'update_rate' in priority_df.columns:
            regional_maturity = {
                "efficiency_leaders": priority_df.nlargest(3, 'update_rate')[['district', 'update_rate']].to_dict('records'),
                "inclusion_risk_zones": priority_df.nsmallest(3, 'update_rate')[['district', 'update_rate']].to_dict('records'),
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
            "regional_benchmarks": regional_maturity,
        }


# Backwards-compatible alias: the class was called GeminiAnalyzer when it ran on
# Vertex AI. Kept so any existing import keeps working.
GeminiAnalyzer = AIAnalyzer
