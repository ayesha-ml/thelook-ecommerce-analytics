import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
from app.bq_app_client import get_client, run_query
from src.sql_loader import load_sql
from src.models.segmentation import (
    scale_features, find_optimal_k,
    fit_segments, profile_segments
)

st.title("Customer Segmentation")
st.markdown(
    "**Business Question:** Which customers are worth investing in, "
    "and what should we do about each group?"
)

client = get_client()

with st.spinner("Loading RFM data from BigQuery..."):
    df_rfm = run_query(client, load_sql('rfm_scoring.sql'))

#  Scale and cluster 
scaled, scaler = scale_features(df_rfm)

k = st.slider("Number of Segments", min_value=2, max_value=6, value=4)
labels, km   = fit_segments(scaled, k)
df_rfm['segment'] = labels
profiles     = profile_segments(df_rfm)
df_rfm['label'] = df_rfm['segment'].map(
    profiles.set_index('segment')['label']
)

# KPI tiles 
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Customers",    f"{len(df_rfm):,}")
col2.metric("Segments",           k)
col3.metric("Avg Spend",          f"${df_rfm['monetary_value'].mean():.0f}")
col4.metric("Avg Recency (days)", f"{df_rfm['recency_days'].mean():.0f}")

st.divider()

# Scatter plot
st.subheader("Segment Distribution")
fig = px.scatter(
    df_rfm.sample(min(5000, len(df_rfm)), random_state=42),
    x='recency_days',
    y='monetary_value',
    color='label',
    size='frequency',
    title='Customer Segments — Recency vs Monetary Value',
    labels={
        'recency_days':   'Days Since Last Purchase',
        'monetary_value': 'Total Spend ($)'
    }
)
st.plotly_chart(fig, use_container_width=True)

st.divider()

# Segment profiles 
st.subheader("Segment Profiles")
display = profiles[['label','count','recency','frequency','monetary']].copy()
display.columns = [
    'Segment', 'Customers',
    'Avg Recency (days)', 'Avg Orders', 'Avg Spend ($)'
]
st.dataframe(display, use_container_width=True, hide_index=True)

st.divider()

#  Revenue at stake 
st.subheader("Revenue at Stake by Segment")
rev = df_rfm.groupby('label')['monetary_value'].sum().reset_index()
rev.columns = ['segment', 'total_revenue']
rev['pct'] = (rev['total_revenue'] / rev['total_revenue'].sum() * 100).round(1)
rev = rev.sort_values('total_revenue', ascending=False)

fig2 = px.bar(
    rev,
    x='segment',
    y='total_revenue',
    text='pct',
    title='Total Historical Revenue by Segment ($)',
    color='segment',
    color_discrete_sequence=px.colors.qualitative.Set2
)
fig2.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
fig2.update_layout(showlegend=False, xaxis_title='', yaxis_title='Revenue ($)')
st.plotly_chart(fig2, use_container_width=True)

st.divider()

# Action recommendations 
st.subheader("Recommended Actions")
actions = {
    'Champions': 'Loyalty perks, early product access, referral incentive',
    'Promising':  'Targeted upsell, second-category purchase onboarding',
    'At Risk':    'Win-back campaign, personalized discount, churn survey',
    'Lost':       'Low-cost re-engagement email only — no paid budget'
}
for label, action in actions.items():
    st.markdown(f"**{label}:** {action}")

# Methodology note
with st.expander("Methodology"):
    st.markdown("""
    - RFM scores computed using NTILE(5) quintile ranking in BigQuery
    - Recency score inverted: fewer days since last purchase = higher score
    - Features scaled using RobustScaler (median + IQR) to handle
      right-skewed monetary values without distortion from outliers
    - K selected using elbow method (inertia) and silhouette score
    - Cluster labels assigned relative to median segment values
    """)