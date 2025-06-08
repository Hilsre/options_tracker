import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import calendar
from utils.db_helper import get_db
from datetime import datetime, timedelta


def load_data():
    conn = get_db()

    # Main query for transaction data with joins
    query = """
    SELECT 
        t.id as transaction_id,
        t.trade_id AS "Trade ID",
        t.date,
        t.price,
        t.qty,
        t.fee,
        t.tax,
        t.total_price,
        t.gain,
        t.open_qty AS open_qty,
        p.name as product_name,
        p.wkn,
        p.strike,
        p.expiry_date,
        bp.name as basis_product,
        pt.name as product_type,
        d.name as direction,
        sc.symbol as strike_currency,
        a.name as action,
        d.name || '@' || CAST(p.strike AS TEXT) || sc.symbol || ' ' || bp.name AS name
    FROM transactions t
    JOIN products p ON t.product_id = p.id
    JOIN basis_products bp ON p.basis_product_id = bp.id
    JOIN product_types pt ON p.product_type_id = pt.id
    JOIN directions d ON p.direction_id = d.id
    JOIN strike_currencies sc ON p.strike_currency_id = sc.id
    JOIN actions a ON t.action_id = a.id
    ORDER BY t.date DESC
    """

    df = pd.read_sql_query(query, conn)
    df['date'] = pd.to_datetime(df['date'])
    return df

def calculate_open_positions(df):
    """
    Calculates open positions based on purchases and sales
    """
    if df.empty:
        return pd.DataFrame()

    # Group by trade_id and calculate net positions
    position_data = df.groupby(['Trade ID','name']).agg({
        'open_qty': lambda x: sum(val if action == 'buy' or action == 'rebuy' else -val for val, action in zip(x, df.loc[x.index, 'action'])),
        'total_price': lambda x: sum(
            val if action == 'buy' or action=='rebuy' else -val for val, action in zip(x, df.loc[x.index, 'action']))
    })

    position_data = position_data.reset_index(level='name')

    # Only positions with quantity > 0 (open positions)
    open_positions = position_data[position_data['open_qty'] > 0]
    print(open_positions)

    return open_positions

def calculate_portfolio_metrics(df):
    """
    Calculates portfolio metrics

    Total value portfolio = sum of all total_price values
    This corresponds to the total volume of all transactions (purchases + sales)
    """
    if df.empty:
        return {
            'total_value': 0,
            'total_gain': 0,
            'total_trades': 0,
            'win_rate': 0,
            'avg_gain_per_trade': 0
        }

    # Total value = sum of all transaction volumes (total_price)
    # This is the total traded volume, not the current portfolio value
    total_value = abs(df['total_price']).sum()
    total_gain = df['gain'].sum()
    total_trades = len(df)

    # Calculate win rate
    profitable_trades = len(df[df['gain'] > 0])
    win_rate = (profitable_trades / total_trades * 100) if total_trades > 0 else 0

    # Average profit per trade
    avg_gain_per_trade = df['gain'].mean() if total_trades > 0 else 0

    return {
        'total_value': total_value,
        'total_gain': total_gain,
        'win_rate': win_rate,
        'avg_gain_per_trade': avg_gain_per_trade
    }

def create_monthly_calendar_view(df, year, month):
    """Creates a real calendar view for a specific month with dark mode"""
    if df.empty:
        return None

    # Filter data for the selected month
    month_start = datetime(year, month, 1)
    if month == 12:
        month_end = datetime(year + 1, 1, 1) - timedelta(days=1)
    else:
        month_end = datetime(year, month + 1, 1) - timedelta(days=1)

    month_df = df[(df['date'] >= month_start) & (df['date'] <= month_end)]

    # Daily aggregation for the month
    daily_data = month_df.groupby(month_df['date'].dt.date).agg({
        'gain': 'sum',
        'transaction_id': 'count'
    }).reset_index()
    daily_data.columns = ['date', 'daily_pnl', 'trade_count']

    # Create dictionary for quick access
    daily_dict = {}
    for _, row in daily_data.iterrows():
        daily_dict[row['date']] = {
            'pnl': row['daily_pnl'],
            'trades': row['trade_count']
        }

    # Create calendar
    cal = calendar.monthcalendar(year, month)
    month_name = calendar.month_name[month]

    # Create Plotly Figure with Dark Mode Theme
    fig = go.Figure()

    # Weekdays Header
    weekdays = ['Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So']

    for week_num, week in enumerate(cal):
        for day_num, day in enumerate(week):
            if day == 0:
                continue

            day_date = datetime(year, month, day).date()
            day_data = daily_dict.get(day_date, {'pnl': 0, 'trades': 0})

            # Determine color based on P&L (dark mode optimized)
            if day_data['pnl'] > 0:
                color = 'rgba(76, 175, 80, 0.9)'  # Green
                text_color = 'white'
            elif day_data['pnl'] < 0:
                color = 'rgba(244, 67, 54, 0.9)'  # Red
                text_color = 'white'
            else:
                color = 'rgba(60, 60, 60, 0.8)'  # Dark gray for dark mode
                text_color = '#E0E0E0'

            # Larger rectangles for better display
            fig.add_shape(
                type="rect",
                x0=day_num * 1.2, y0=-(week_num + 1) * 1.5, x1=day_num * 1.2 + 1.1, y1=-(week_num + 0.1) * 1.5,
                fillcolor=color,
                line=dict(color="rgba(255,255,255,0.3)", width=1)
            )

            # Tag number - larger and better positioned
            fig.add_annotation(
                x=day_num * 1.2 + 0.55, y=-(week_num + 0.15) * 1.5,
                text=f"<b>{day}</b>",
                showarrow=False,
                font=dict(size=16, color=text_color),
                xanchor="center", yanchor="top"
            )

            # Display P&L and trades (if available) - better positioning
            if day_data['trades'] > 0:
                # P&L in larger font
                fig.add_annotation(
                    x=day_num * 1.2 + 0.55, y=-(week_num + 0.5) * 1.5,
                    text=f"<b>€{day_data['pnl']:.0f}</b>",
                    showarrow=False,
                    font=dict(size=20, color=text_color),
                    xanchor="center", yanchor="middle"
                )

                # Trade Count in smaller font
                fig.add_annotation(
                    x=day_num * 1.2 + 0.55, y=-(week_num + 0.8) * 1.5,
                    text=f"{day_data['trades']} T",
                    showarrow=False,
                    font=dict(size=15, color=text_color),
                    xanchor="center", yanchor="bottom"
                )

    # Add weekday header - customized positioning
    for i, weekday in enumerate(weekdays):
        fig.add_annotation(
            x=i * 1.2 + 0.55, y=0.4,
            text=f"<b>{weekday}</b>",
            showarrow=False,
            font=dict(size=14, color="#E0E0E0"),
            xanchor="center", yanchor="bottom"
        )

    # Configure layout - Dark Mode Theme
    fig.update_layout(
        title={
            'text': f"Trading Kalender - {month_name} {year}",
            'font': {'color': '#E0E0E0', 'size': 18}
        },
        xaxis=dict(
            range=[-0.2, 8.5],
            showgrid=False,
            showticklabels=False,
            zeroline=False
        ),
        yaxis=dict(
            range=[-(len(cal) + 0.5) * 1.5, 0.6],
            showgrid=False,
            showticklabels=False,
            zeroline=False
        ),
        height=800,
        plot_bgcolor='rgba(30, 30, 30, 1)',  # Dark background
        paper_bgcolor='rgba(30, 30, 30, 1)',  # Dark paper background
        showlegend=False,
        margin=dict(l=20, r=20, t=60, b=20)
    )

    return fig

def create_monthly_calendar_view_test(df, year, month):
    """Creates a real calendar view for a specific month with auto theme (light/dark)"""
    mode = st.session_state.get("theme_mode")
    if df.empty:
        return None

    # Filter data for the selected month
    month_start = datetime(year, month, 1)
    month_end = datetime(year + 1, 1, 1) - timedelta(days=1) if month == 12 else datetime(year, month + 1, 1) - timedelta(days=1)
    month_df = df[(df['date'] >= month_start) & (df['date'] <= month_end)]

    # Daily aggregation for the month
    daily_data = month_df.groupby(month_df['date'].dt.date).agg({
        'gain': 'sum',
        'transaction_id': 'count'
    }).reset_index()
    daily_data.columns = ['date', 'daily_pnl', 'trade_count']

    # Create dictionary for quick access
    daily_dict = {
        row['date']: {
            'pnl': row['daily_pnl'],
            'trades': row['trade_count']
        }
        for _, row in daily_data.iterrows()
    }

    # Farben je nach Modus
    if mode == 'dark':
        pos_color = 'rgba(76, 175, 80, 0.9)'
        neg_color = 'rgba(244, 67, 54, 0.9)'
        neutral_color = 'rgba(60, 60, 60, 0.8)'
        text_color = 'white'
        template = 'plotly_dark'
        bg_color = 'rgba(0,0,0,0)'
    else:
        pos_color = 'rgba(56, 142, 60, 0.85)'
        neg_color = 'rgba(211, 47, 47, 0.85)'
        neutral_color = 'rgba(240, 240, 240, 0.8)'
        text_color = 'black'
        template = 'plotly_white'
        bg_color = 'rgba(255,255,255,1)'

    cal = calendar.monthcalendar(year, month)
    month_name = calendar.month_name[month]
    fig = go.Figure(layout_template=template)

    weekdays = ['Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So']

    for week_num, week in enumerate(cal):
        for day_num, day in enumerate(week):
            if day == 0:
                continue

            day_date = datetime(year, month, day).date()
            day_data = daily_dict.get(day_date, {'pnl': 0, 'trades': 0})

            color = pos_color if day_data['pnl'] > 0 else neg_color if day_data['pnl'] < 0 else neutral_color

            fig.add_shape(
                type="rect",
                x0=day_num * 1.2, y0=-(week_num + 1) * 1.5,
                x1=day_num * 1.2 + 1.1, y1=-(week_num + 0.1) * 1.5,
                fillcolor=color,
                line=dict(width=1, color='rgba(100,100,100,0.3)')
            )

            fig.add_annotation(
                x=day_num * 1.2 + 0.55, y=-(week_num + 0.15) * 1.5,
                text=f"<b>{day}</b>",
                showarrow=False,
                font=dict(size=16, color=text_color),
                xanchor="center", yanchor="top"
            )

            if day_data['trades'] > 0:
                fig.add_annotation(
                    x=day_num * 1.2 + 0.55, y=-(week_num + 0.5) * 1.5,
                    text=f"<b>€{day_data['pnl']:.0f}</b>",
                    showarrow=False,
                    font=dict(size=20, color=text_color),
                    xanchor="center", yanchor="middle"
                )
                fig.add_annotation(
                    x=day_num * 1.2 + 0.55, y=-(week_num + 0.8) * 1.5,
                    text=f"{day_data['trades']} T",
                    showarrow=False,
                    font=dict(size=15, color=text_color),
                    xanchor="center", yanchor="bottom"
                )

    for i, weekday in enumerate(weekdays):
        fig.add_annotation(
            x=i * 1.2 + 0.55, y=0.4,
            text=f"<b>{weekday}</b>",
            showarrow=False,
            font=dict(size=14, color=text_color),
            xanchor="center", yanchor="bottom"
        )

    fig.update_layout(
        title={
            'text': f"Trading Kalender - {month_name} {year}",
            'font': {'color': text_color, 'size': 18}
        },
        xaxis=dict(
            range=[-0.2, 8.5],
            showgrid=False,
            showticklabels=False,
            zeroline=False
        ),
        yaxis=dict(
            range=[-(len(cal) + 0.5) * 1.5, 0.6],
            showgrid=False,
            showticklabels=False,
            zeroline=False
        ),
        height=800,
        showlegend=False,
        margin=dict(l=20, r=20, t=60, b=20),
        plot_bgcolor=bg_color,
        paper_bgcolor=bg_color
    )

    return fig

def get_date_range_label(df, timeframe):
    """Generates customized date labels for x-axis"""
    if df.empty:
        return "No data"

    if timeframe == "Letzte 30 Tage" or timeframe == "Last 30 Days":
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        return f"{start_date.strftime('%d.%m.%Y')} - {end_date.strftime('%d.%m.%Y')}"
    elif timeframe == "Letzte 365 Tage" or timeframe == "Last 365 Days":
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)
        return f"{start_date.strftime('%d.%m.%Y')} - {end_date.strftime('%d.%m.%Y')}"
    else:  # Total
        start_date = df['date'].min()
        end_date = df['date'].max()
        return f"{start_date.strftime('%d.%m.%Y')} - {end_date.strftime('%d.%m.%Y')}"
