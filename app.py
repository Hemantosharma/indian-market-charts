import streamlit as st
import numpy as np
import plotly.graph_objects as go
import time
import upstox_backend as backend

st.set_page_config(page_title="Model 2 Suite Pro", layout="centered", initial_sidebar_state="collapsed")
st.markdown("<style>div[data-testid='stMetricValue']{font-size:18px !important;}body{background-color:#0d1117;color:white;}</style>", unsafe_allow_html=True)

st.title("🎯 Pro Analytics Suite")

user_token = st.text_input("Paste Daily Upstox Token Here", type="password")

if not user_token:
    st.warning("🔒 App Locked. Please enter your active 24-hour Upstox token above to continue.")
    st.stop()

# 1. ASSET SELECTOR AND CONFIRMATION KEY
index_choice = st.selectbox("1. Choose Market Profile Asset", ["NIFTY 50", "BANKNIFTY", "SENSEX"])
confirm_asset = st.button("Confirm Asset Selection")

if "active_asset" not in st.session_state:
    st.session_state["active_asset"] = "NIFTY 50"
if confirm_asset or "available_dates" not in st.session_state:
    st.session_state["active_asset"] = index_choice
    with st.spinner("Loading unique contract loops for next 3 months..."):
        st.session_state["available_dates"] = backend.get_active_expiry_list(st.session_state["active_asset"], user_token)

# 2. DYNAMIC CORRESPONDING EXPIRY LIST
expiry_choice = st.selectbox(f"2. Select Expiry Date for {st.session_state['active_asset']}", st.session_state["available_dates"])

mode = st.radio("3. Select Mode View", ["Liquidation Heatmap", "Harmonic Scanner Chart"], horizontal=True)

df_oi, spot, df_candles = backend.fetch_market_matrix(st.session_state["active_asset"], expiry_choice, user_token)

if df_oi is not None and spot is not None:
    st.write(f"### Active Position Spot ({st.session_state['active_asset']}): **{spot:,.2f}**")
    
    if mode == "Liquidation Heatmap":
        prices = np.linspace(int(spot * 0.98), int(spot * 1.02), 80)
        matrix = np.zeros((len(prices), 20))
        for i, p in enumerate(prices):
            intensity = 0
            for _, r in df_oi.iterrows():
                if r['strike'] > p and r['strike'] > spot:
                    if p >= r['strike'] * 0.94: intensity += r['call_oi']
                elif r['strike'] < p and r['strike'] < spot:
                    if p <= r['strike'] * 1.06: intensity += r['put_oi']
            for col in range(20): 
                matrix[i, col] = intensity * (0.3 + (col / 20.0) * 0.7)
            
        fig = go.Figure(data=go.Heatmap(z=matrix, y=prices, colorscale='Turbo'))
        fig.add_hline(y=spot, line_dash="dash", line_color="#00ffcc", annotation_text="Spot Axis")
        fig.update_layout(height=450, margin=dict(l=5, r=5, t=5, b=5))
        st.plotly_chart(fig, use_container_width=True)
        
    elif mode == "Harmonic Scanner Chart":
        h_data = backend.generate_harmonic_chart_data(df_candles, spot)
        
        st.success(f"🔥 **Pattern Triggered:** {h_data['pattern']}")
        
        c1, c2, c3 = st.columns(3)
        c1.metric("🎯 Entry Target", f"{h_data['entry']:,.2f}")
        c2.metric("📈 Take Profit", f"{h_data['target']:,.2f}")
        c3.metric("🛑 Stop Loss", f"{h_data['stop']:,.2f}")
        
        fig_chart = go.Figure()
        
        fig_chart.add_trace(go.Scatter(
            x=h_data["full_timeline"], y=h_data["full_prices"],
            mode='lines', name='Candle Movement', line=dict(color='#4c566a', width=1.5)
        ))
        
        fig_chart.add_trace(go.Scatter(
            x=h_data["x_points"], y=h_data["y_points"],
            mode='lines+markers+text', name='Harmonic Legs',
            text=["X", "A", "B", "C", "D"], textposition="top center",
            line=dict(color='#ff9900', width=3),
            marker=dict(size=10, color='#ffffff', line=dict(color='#ff9900', width=2))
        ))
        
        fig_chart.add_hline(y=h_data['target'], line_dash="dot", line_color="#00ff00", line_width=2, annotation_text="🎯 Target")
        fig_chart.add_hline(y=h_data['entry'], line_dash="dash", line_color="#00ffcc", line_width=1.5, annotation_text="🟢 Entry")
        fig_chart.add_hline(y=h_data['stop'], line_dash="dot", line_color="#ff0000", line_width=2, annotation_text="🛑 Stop Loss")
        
        fig_chart.update_layout(
            height=400, margin=dict(l=10, r=10, t=10, b=10),
            plot_bgcolor="rgba(13,17,23,1)", paper_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(showgrid=False, zeroline=False), yaxis=dict(showgrid=True, gridcolor='#21262d')
        )
        st.plotly_chart(fig_chart, use_container_width=True)
            
    time.sleep(15)
    st.rerun()
else:
    st.error("Data pipeline timeout. Re-verify access token parameters inside the entry field.")
