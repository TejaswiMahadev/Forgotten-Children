# 🧒 The Forgotten Children of Aadhaar  
### Detecting Silent Exclusion Through Biometric Update Gaps

## 📌 Overview

**The Forgotten Children of Aadhaar** is a privacy-preserving, data-driven decision support system built using **aggregated UIDAI Aadhaar datasets** to identify **silent exclusion risks among children aged 5–17 years** who have not completed mandatory biometric updates.

Missed biometric updates often remain unnoticed until authentication failures occur later in life. This project proactively detects such risks using **time-series analysis, anomaly detection, explainable forecasting, and geospatial analytics**, enabling early, targeted interventions.

The system translates complex analytics into **actionable, policy-ready insights** through an interactive dashboard and an AI-assisted explanation layer—without accessing any individual-level data.

## 🎯 Problem Statement

Children aged 5–17 are required to update Aadhaar biometrics to ensure long-term identity usability. However:

- Missed updates are **not immediately visible**
- Exclusion risks surface only later during service access
- Existing reports focus on completed updates, not unmet obligations

This project addresses the gap by identifying:
- **Silent exclusion risks**
- **Geographic and demographic hotspots**
- **Migration-driven stress on update infrastructure**
- **Future risks using explainable forecasting**

## 🧠 Key Insights Generated

- **Baseline Biometric Gap** – Quantifies the number of children at risk of future exclusion  
- **System Efficiency** – Separates awareness from operational performance  
- **Anomaly Detection** – Identifies unusual stagnation or stress patterns  
- **Migration Signals** – Infers mobility from update behaviour (without tracking individuals)  
- **Horizon Risk** – Forecasts future gaps if current trends continue  
- **Priority Scoring** – Ranks PIN codes for targeted intervention  

## 📊 Dashboard & Visual Analytics

The interactive dashboard provides:

- 📍 **Geographic risk maps** (PIN & district level)  
- 📈 **Time-series trends & forecasts**  
- 🚨 **Anomaly detection panels**  
- 🧩 **Hierarchical treemaps (State → District → PIN)**  
- 🎯 **PIN-level tactical scorecards with recommendations**

All visuals are built using **Plotly + Dash** and designed for decision-makers, not just analysts.

## 🏗️ Architecture Overview

                          UIDAI Aggregated Data
                                    ↓
                        Data Loading & Validation
                                    ↓
                        Cleaning & Preprocessing
                                    ↓
                            Feature Engineering
                                    ↓
              Gap Analysis | Anomaly Detection | Forecasting
                                    ↓
                      Signal Fusion & Priority Scoring
                                    ↓
                        Interactive Dash Dashboard
                                    ↓
                      AI-Assisted Insight Explanations

