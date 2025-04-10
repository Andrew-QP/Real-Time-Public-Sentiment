import streamlit as st
import plotly.graph_objs as go
import sqlite3
from datetime import datetime
import pandas as pd
import time
from streamlit_autorefresh import st_autorefresh

def get_update_flag():
    conn = sqlite3.connect("rtsProjectDB.db")
    cursor = conn.cursor()
    cursor.execute("SELECT update_graph FROM flags WHERE id = 1")
    flag = cursor.fetchone()[0]
    conn.close()
    return flag

def reset_update_flag():
    conn = sqlite3.connect("rtsProjectDB.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE flags SET update_graph = 0 WHERE id = 1")
    conn.commit()
    conn.close()

def get_stock_data():
    conn = sqlite3.connect("rtsProjectDB.db")
    cursor = conn.cursor()
    cursor.execute("SELECT time, close FROM stockPrice ORDER BY time DESC LIMIT 100")
    data = cursor.fetchall()
    conn.close()

    # Convert time from string to datetime
    for i in range(len(data)):
        data[i] = (datetime.strptime(data[i][0], '%Y-%m-%d %I:%M %p'), data[i][1])

    data.reverse()
    return pd.DataFrame(data, columns=["Time", "Close"])

def plot_stock_data():
    stock_data_df = get_stock_data()
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=stock_data_df['Time'], 
        y=stock_data_df['Close'], 
        mode='lines+markers',
        name="Close Price",
        line=dict(color='blue', width=2),
        marker=dict(size=5)
    ))

    start_idx = max(0, len(stock_data_df) - 50)
    fig.update_layout(
        title="Real-Time Stock Price",
        xaxis_title="Time (CT)",
        yaxis_title="Stock Price (USD)",
        xaxis=dict(
            tickmode='array', 
            tickangle=45, 
            tickvals=stock_data_df['Time'][::5],
            range=[stock_data_df['Time'].iloc[start_idx], stock_data_df['Time'].iloc[-1]]
        ),
        autosize=True,
        margin=dict(l=40, r=40, b=80, t=80),
        template="plotly_dark"
    )

    return fig

# Streamlit display loop
st.set_page_config(layout="wide")
st.title('Real-Time Stock Price')
st.write("Displaying the real-time stock price updates for TSLA")

graph_placeholder = st.empty()

st_autorefresh(interval=10000, key="refresh")  # 10 seconds

if get_update_flag() == 1:
    fig = plot_stock_data()
    graph_placeholder.plotly_chart(fig, use_container_width=True)
    reset_update_flag()
