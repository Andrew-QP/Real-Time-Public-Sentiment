import streamlit as st
import plotly.graph_objs as go
import sqlite3
from datetime import datetime, date
import pandas as pd
import pytz
from streamlit_autorefresh import st_autorefresh

st.set_page_config(layout="wide")
st.title('Real-Time Stock Price')
st.write("Displaying today's real-time stock price updates for TSLA")

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

def get_stock_data_today():
    conn = sqlite3.connect("rtsProjectDB.db")
    cursor = conn.cursor()

    # Get today's date in Central Time (CT)
    today_str = datetime.now(pytz.timezone('US/Central')).strftime('%Y-%m-%d')

    cursor.execute("""
        SELECT time, close 
        FROM stockPrice 
        WHERE time LIKE ? 
        ORDER BY time ASC
    """, (today_str + '%',))
        
    data = cursor.fetchall()
    cursor.close()

    # Convert data to DataFrame
    stock_data_df = pd.DataFrame(data, columns=["Time", "Close"])

    # Convert 'Time' column from string to datetime in Central Time
    stock_data_df['Time'] = pd.to_datetime(stock_data_df['Time'], format='%Y-%m-%d %I:%M %p')

    stock_data_df = stock_data_df.sort_values(by='Time')

    stock_data_df['TimeLabel'] = stock_data_df['Time'].dt.strftime('%H:%M')

    return stock_data_df


def plot_stock_data(df):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df['TimeLabel'], 
        y=df['Close'], 
        mode='lines+markers',
        name="Close Price",
        line=dict(color='blue', width=2),
        marker=dict(size=5)
    ))

    start_idx = max(0, len(df) - 75)
    fig.update_layout(
        title="Real-Time Stock Price (Today)",
        xaxis_title="Time (CT)",
        yaxis_title="Stock Price (USD)",
        xaxis=dict(
            tickmode='array', 
            tickangle=45, 
            tickvals=df['TimeLabel'][::5],
            range=[df['TimeLabel'].iloc[start_idx], df['TimeLabel'].iloc[-1]]
        ),
        autosize=True,
        margin=dict(l=40, r=40, b=80, t=80),
        template="plotly_dark"
    )
    return fig

# Graph and autorefresh
st_autorefresh(interval=10000, key="refresh")  # refresh every 10 seconds

# Always fetch fresh data if flag is 1
if get_update_flag() == 1:
    todaydf = get_stock_data_today()
    st.session_state['data_cached'] = todaydf
    reset_update_flag()
else:
    # fallback to session cache if already loaded once
    if 'data_cached' not in st.session_state:
        st.session_state['data_cached'] = get_stock_data_today()
    todaydf = st.session_state['data_cached']


# Display graph
if not todaydf.empty:
    fig = plot_stock_data(todaydf)
    st.plotly_chart(fig, use_container_width=True)
    st.write(todaydf[['Time', 'Close']].tail(10))
else:
    st.warning("No stock data available for today yet.")
