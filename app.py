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

    return stock_data_df

def get_simple_predictions():
    conn = sqlite3.connect("rtsProjectDB.db")
    cursor = conn.cursor()

    # Get today's date in Central Time (CT)
    today_str = datetime.now(pytz.timezone('US/Central')).strftime('%Y-%m-%d')

    cursor.execute("""
        SELECT time, prediction 
        FROM simplePrediction 
        WHERE time LIKE ? 
        ORDER BY time ASC
    """, (today_str + '%',))
        
    data = cursor.fetchall()
    cursor.close()

    # Convert data to DataFrame
    predictions_df = pd.DataFrame(data, columns=["Time", "Prediction"])

    # Convert 'Time' column from string to datetime in Central Time
    predictions_df['Time'] = pd.to_datetime(predictions_df['Time'], format='%Y-%m-%d %I:%M %p')

    predictions_df.sort_values(by='Time', inplace=True)

    return predictions_df

def get_sentiment_predictions():
    conn = sqlite3.connect("rtsProjectDB.db")
    cursor = conn.cursor()

    # Get today's date in Central Time (CT)
    today_str = datetime.now(pytz.timezone('US/Central')).strftime('%Y-%m-%d')

    cursor.execute("""
        SELECT time, prediction 
        FROM sentimentPrediction 
        WHERE time LIKE ? 
        ORDER BY time ASC
    """, (today_str + '%',))
        
    data = cursor.fetchall()
    cursor.close()

    # Convert data to DataFrame
    predictions_df = pd.DataFrame(data, columns=["Time", "Prediction"])

    # Convert 'Time' column from string to datetime in Central Time
    predictions_df['Time'] = pd.to_datetime(predictions_df['Time'], format='%Y-%m-%d %I:%M %p')

    predictions_df.sort_values(by='Time', inplace=True)

    return predictions_df

def plot_stock_data(df, simplePredictionsdf, sentiPredictiondf):
    fig = go.Figure()

    # Real Stock Price Line
    fig.add_trace(go.Scatter(
        x=df['Time'], 
        y=df['Close'], 
        mode='lines+markers',
        name="Close Price",
        line=dict(color='blue', width=2),
        marker=dict(size=5)
    ))

    # Simple Model Prediction Line
    fig.add_trace(go.Scatter(
        x=simplePredictionsdf['Time'], 
        y=simplePredictionsdf['Prediction'], 
        mode='lines+markers',
        name="Prediction with Finance Only",
        line=dict(color='red', width=2, dash='dash'),
        marker=dict(size=5)
    ))

    # Sentiment Model Prediction Line
    fig.add_trace(go.Scatter(
        x=sentiPredictiondf['Time'], 
        y=sentiPredictiondf['Prediction'], 
        mode='lines+markers',
        name="Prediction with Sentiment & Finance",
        line=dict(color='green', width=2, dash='dash'),
        marker=dict(size=5)
    ))

    today_str = datetime.now().strftime("%B %d, %Y")
    fig.update_layout(
        title=f"Real-Time Stock Price ({today_str})",
        xaxis_title="Time (CT)",
        yaxis_title="Stock Price (USD)",
        xaxis=dict(
            tickmode='array', 
            tickangle=45, 
            tickformat="%H:%M",
            tickvals=df['Time'][::5]
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
    simplePredictiondf = get_simple_predictions()
    sentiPredictiondf = get_sentiment_predictions()
    st.session_state['data_cached'] = todaydf
    st.session_state['simple_predictions_cached'] = simplePredictiondf
    st.session_state['sentiment_predictions_cached'] = sentiPredictiondf
    reset_update_flag()
else:
    # fallback to session cache if already loaded once
    if 'data_cached' not in st.session_state:
        st.session_state['data_cached'] = get_stock_data_today()
    if 'simple_predictions_cached' not in st.session_state:
        st.session_state['simple_predictions_cached'] = get_simple_predictions()
    if 'sentiment_predictions_cached' not in st.session_state:
        st.session_state['sentiment_predictions_cached'] = get_sentiment_predictions()
    todaydf = st.session_state['data_cached']
    simplePredictiondf = st.session_state['simple_predictions_cached']
    sentiPredictiondf = st.session_state['sentiment_predictions_cached']


# Display graph
if not todaydf.empty:
    fig = plot_stock_data(todaydf, simplePredictiondf, sentiPredictiondf)
    st.plotly_chart(fig, use_container_width=True)
    # combined_df = pd.merge(todaydf[['Time', 'Close']], simplePredictiondf[['Time', 'Prediction']], on='Time', how='right')
    # Rename prediction columns to distinguish them
    simplePredictiondf = simplePredictiondf.rename(columns={"Prediction": "Simple Model Prediction"})
    sentiPredictiondf = sentiPredictiondf.rename(columns={"Prediction": "Sentiment Model Prediction"})

    # Outer merge to include all timestamps even if some are missing
    combined_df = pd.merge(todaydf[['Time', 'Close']], 
                        simplePredictiondf[['Time', 'Simple Model Prediction']], 
                        on='Time', how='outer')

    combined_df = pd.merge(combined_df, 
                        sentiPredictiondf[['Time', 'Sentiment Model Prediction']], 
                        on='Time', how='outer')
    # Drop rows where both predictions are empty
    combined_df.dropna(subset=['Simple Model Prediction', 'Sentiment Model Prediction'], how='all', inplace=True)
    # Sort by time
    combined_df.sort_values('Time', inplace=True)

    # Show last 10 entries
    st.write("Last 10 Predictions")
    st.dataframe(combined_df.tail(10), use_container_width=True)
else:
    st.warning("No stock data available for today yet.")
