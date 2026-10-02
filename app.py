import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
import plotly.express as px

st.set_page_config(
    page_title="Stock Dashboard",
    page_icon="📈",
    layout="wide",
)

DEFAULT_TICKERS = ["AAPL", "MSFT", "GOOG", "AMZN", "NVDA", "META"]


def fetch_stock_data(ticker: str, start: str, end: str, interval: str = "1d"):
    try:
        data = yf.download(
            ticker,
            start=start,
            end=end,
            interval=interval,
            progress=False,
            auto_adjust=False,
        )
        if data.empty:
            raise ValueError(f"No data available for {ticker}")

        data = data.reset_index()
        data.columns = [str(col).lower() for col in data.columns]

        if "date" not in data.columns and "datetime" in data.columns:
            data.rename(columns={"datetime": "date"}, inplace=True)

        if "date" not in data.columns:
            data.insert(0, "date", pd.date_range(start=start, periods=len(data), freq="D"))

        return data
    except Exception as e:
        st.error(f"Failed to load data for {ticker}: {e}")
        return None


def add_indicators(df: pd.DataFrame):
    df = df.copy()
    if df.empty:
        return df

    df["sma_20"] = df["close"].rolling(window=20).mean()
    df["sma_50"] = df["close"].rolling(window=50).mean()

    delta = df["close"].pct_change()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(window=14, min_periods=14).mean()
    avg_loss = loss.rolling(window=14, min_periods=14).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    df["rsi_14"] = 100 - (100 / (1 + rs))
    df["rsi_14"] = df["rsi_14"].fillna(50)

    return df


def get_company_info(ticker: str):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        return {
            "name": info.get("longName", ticker),
            "sector": info.get("sector", "N/A"),
            "currency": info.get("currency", "USD"),
            "market_cap": info.get("marketCap", 0),
            "previous_close": info.get("regularMarketPreviousClose", 0),
        }
    except Exception:
        return {
            "name": ticker,
            "sector": "N/A",
            "currency": "USD",
            "market_cap": 0,
            "previous_close": 0,
        }


def get_summary(df: pd.DataFrame):
    if df.empty or len(df) < 2:
        return {
            "current_price": 0,
            "change": 0,
            "percent_change": 0,
            "high": 0,
            "low": 0,
            "volume": 0,
        }

    latest = df.iloc[-1]
    previous = df.iloc[-2]

    current_price = float(latest["close"])
    prev_close = float(previous["close"])
    change = current_price - prev_close
    pct_change = (change / prev_close) * 100 if prev_close else 0

    return {
        "current_price": current_price,
        "change": change,
        "percent_change": pct_change,
        "high": float(df["high"].max()),
        "low": float(df["low"].min()),
        "volume": int(latest["volume"]),
    }


def plot_candlestick(df: pd.DataFrame):
    fig = go.Figure(
        data=[
            go.Candlestick(
                x=df["date"],
                open=df["open"],
                high=df["high"],
                low=df["low"],
                close=df["close"],
                name="Price",
                increasing_line_color="#2ecc71",
                decreasing_line_color="#e74c3c",
            )
        ]
    )

    fig.add_trace(
        go.Scatter(
            x=df["date"],
            y=df["sma_20"],
            mode="lines",
            name="SMA 20",
            line=dict(color="#3498db", width=2),
        )
    )

    fig.add_trace(
        go.Scatter(
            x=df["date"],
            y=df["sma_50"],
            mode="lines",
            name="SMA 50",
            line=dict(color="#f39c12", width=2),
        )
    )

    fig.update_layout(
        title="Price Trend",
        xaxis_title="Date",
        yaxis_title="Price",
        template="plotly_white",
        height=500,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=20, r=20, t=50, b=20),
    )
    return fig


def plot_volume(df: pd.DataFrame):
    fig = px.bar(
        df,
        x="date",
        y="volume",
        title="Trading Volume",
        color="volume",
        color_continuous_scale="Viridis",
    )
    fig.update_layout(template="plotly_white", height=300, margin=dict(l=20, r=20, t=50, b=20))
    return fig


def plot_rsi(df: pd.DataFrame):
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df["date"],
            y=df["rsi_14"],
            mode="lines",
            name="RSI(14)",
            line=dict(color="#9b59b6", width=2),
        )
    )
    fig.add_hline(y=70, line_dash="dash", line_color="red")
    fig.add_hline(y=30, line_dash="dash", line_color="green")
    fig.update_layout(
        title="Relative Strength Index (RSI)",
        xaxis_title="Date",
        yaxis_title="RSI",
        template="plotly_white",
        height=250,
        margin=dict(l=20, r=20, t=50, b=20),
    )
    return fig


def plot_correlation_matrix(selected_df: dict):
    if len(selected_df) < 2:
        return None

    combined = pd.DataFrame()
    for ticker, df in selected_df.items():
        if "close" in df.columns:
            combined[ticker] = df.set_index("date")["close"]

    corr = combined.corr().round(3)
    fig = px.imshow(
        corr,
        text_auto=True,
        color_continuous_scale="RdBu_r",
        zmin=-1,
        zmax=1,
        aspect="auto",
        title="Correlation Matrix",
    )
    fig.update_layout(template="plotly_white", height=400, margin=dict(l=20, r=20, t=50, b=20))
    return fig


def format_currency(value):
    return f"${value:,.2f}"


def format_percent(value):
    return f"{value:+.2f}%"


def main():
    st.title("📈 Stock Dashboard")

    with st.sidebar:
        st.header("Controls")
        tickers = st.multiselect(
            "Select stocks",
            options=DEFAULT_TICKERS,
            default=["AAPL", "MSFT", "GOOG"],
        )

        if not tickers:
            st.warning("Please choose at least one stock.")
            st.stop()

        start_date = st.date_input("Start date", value=pd.to_datetime("2024-01-01"))
        end_date = st.date_input("End date", value=pd.to_datetime("today"))
        interval = st.selectbox("Interval", ["1d", "1wk", "1mo"])

    if start_date >= end_date:
        st.error("End date must be after start date.")
        st.stop()

    start_str = start_date.strftime("%Y-%m-%d")
    end_str = end_date.strftime("%Y-%m-%d")

    stock_data = {}
    for ticker in tickers:
        df = fetch_stock_data(ticker, start_str, end_str, interval)
        if df is not None:
            df = add_indicators(df)
            stock_data[ticker] = df

    if not stock_data:
        st.stop()

    primary = tickers[0]
    primary_df = stock_data[primary]
    summary = get_summary(primary_df)
    info = get_company_info(primary)

    st.subheader(f"{info['name']} ({primary})")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Current Price", format_currency(summary["current_price"]))
    with col2:
        st.metric("Daily Change", format_currency(summary["change"]), format_percent(summary["percent_change"]))
    with col3:
        st.metric("Day High", format_currency(summary["high"]))
    with col4:
        st.metric("Day Low", format_currency(summary["low"]))

    company_col, market_col = st.columns(2)
    with company_col:
        st.write(f"Company: {info['name']}")
        st.write(f"Sector: {info['sector']}")
        st.write(f"Currency: {info['currency']}")
    with market_col:
        st.write(f"Volume: {summary['volume']:,}")
        st.write(f"Market Cap: ${info['market_cap']:,}" if info["market_cap"] else "Market Cap: N/A")

    st.plotly_chart(plot_candlestick(primary_df), use_container_width=True)

    vol_col, rsi_col = st.columns(2)
    with vol_col:
        st.plotly_chart(plot_volume(primary_df), use_container_width=True)
    with rsi_col:
        st.plotly_chart(plot_rsi(primary_df), use_container_width=True)

    st.subheader("Portfolio Overview")
    rows = []
    for ticker, df in stock_data.items():
        s = get_summary(df)
        info = get_company_info(ticker)
        rows.append(
            {
                "Ticker": ticker,
                "Company": info["name"],
                "Price": s["current_price"],
                "Change %": s["percent_change"],
                "Volume": s["volume"],
                "High": s["high"],
                "Low": s["low"],
            }
        )

    table = pd.DataFrame(rows)
    st.dataframe(table.sort_values("Change %", ascending=False), use_container_width=True)

    if len(stock_data) > 1:
        st.subheader("Cross-Stock Comparison")
        corr_fig = plot_correlation_matrix(stock_data)
        if corr_fig:
            st.plotly_chart(corr_fig, use_container_width=True)


if __name__ == "__main__":
    main()
