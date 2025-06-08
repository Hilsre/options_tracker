import streamlit as st
import plotly.express as px
from datetime import datetime, timedelta
from utils.overview_helper import (load_data, calculate_open_positions, calculate_portfolio_metrics, get_date_range_label)
from utils.settings_handler import get_lang
import calendar
import plotly.graph_objects as go

st.set_page_config(page_title="Derivate Tracker Dashboard", page_icon="📈", layout="wide", initial_sidebar_state="expanded")

T = get_lang()

st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin: 0.5rem;
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
        border: 1px solid rgba(255, 255, 255, 0.2);
        backdrop-filter: blur(10px);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 35px rgba(102, 126, 234, 0.4);
    }
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
        margin: 0.5rem 0;
    }
    .metric-label {
        font-size: 0.9rem;
        opacity: 0.9;
        margin-bottom: 0.5rem;
    }
    .metric-delta {
        font-size: 0.8rem;
        opacity: 0.8;
    }
    .sidebar-section {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    .open-positions-card {
        background: linear-gradient(135deg, #ff9800 0%, #ff5722 100%);
        padding: 1.5rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin: 0.5rem;
        box-shadow: 0 8px 25px rgba(255, 152, 0, 0.3);
        border: 1px solid rgba(255, 255, 255, 0.2);
        backdrop-filter: blur(10px);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    .open-positions-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 35px rgba(255, 152, 0, 0.4);
    }
</style>
""", unsafe_allow_html=True)

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
    weekdays = T["weekdays_short"]

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
        height=760,
        plot_bgcolor='rgba(30, 30, 30, 1)',  # Dark background
        paper_bgcolor='rgba(30, 30, 30, 1)',  # Dark paper background
        showlegend=False,
        margin=dict(l=20, r=20, t=20, b=20)
    )

    return fig



def main():
    # Header
    st.title(T["title_overview_site"])

    # load data
    try:
        df = load_data()
    except Exception as e:
        st.error(f"{T['error_loading']} {e}")
        st.info(T["db_loading_error"])
        return

    if df.empty:
        st.warning(T["db_no_data_error"])
        return

    # Calculate portfolio metrics (based on all data)
    metrics = calculate_portfolio_metrics(df)

    # Calculate open positions
    open_positions = calculate_open_positions(df)

    # Key performance indicators with tile design
    st.subheader(T["kpi_subheader"])

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">{T['total_trading_volume']}</div>
            <div class="metric-value">€ {metrics['total_value']:,.0f}</div>
            <div class="metric-delta">{T['sum_of_all_transactions']}</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        delta_color = "🟢" if metrics['total_gain'] >= 0 else "🔴"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">{T['total_p_l']}</div>
            <div class="metric-value">{delta_color} € {metrics['total_gain']:,.2f}</div>
            <div class="metric-delta">{T['realised_p_l']}</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        win_color = "🟢" if metrics['win_rate'] >= 50 else "🟡" if metrics['win_rate'] >= 30 else "🔴"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">{T['win_rate']}</div>
            <div class="metric-value">{win_color} {metrics['win_rate']:.1f}%</div>
            <div class="metric-delta">{T['profitable_trades']}</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        avg_color = "🟢" if metrics['avg_gain_per_trade'] >= 0 else "🔴"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">{T['avg_win_per_trade']}</div>
            <div class="metric-value">{avg_color} € {metrics['avg_gain_per_trade']:,.2f}</div>
            <div class="metric-delta">{T['avg_per_trade']}</div>
        </div>
        """, unsafe_allow_html=True)

    with col5:
        open_positions_count = len(open_positions)
        open_positions_value = open_positions['total_price'].sum() if not open_positions.empty else 0
        st.markdown(f"""
        <div class="open-positions-card">
            <div class="metric-label">{T['open_positions']}</div>
            <div class="metric-value">📊 {open_positions_count}</div>
            <div class="metric-delta">€ {open_positions_value:,.2f} Volumen</div>
        </div>
        """, unsafe_allow_html=True)

    # Open positions detail view
    if not open_positions.empty:
        st.subheader(T["open_positions_details"])

        open_positions_display = open_positions.copy()
        open_positions_display['total_price'] = open_positions_display['total_price'].apply(lambda x: f"€ {x:,.2f}")
        open_positions_display.columns = T["open_positions_display_columns"]

        st.dataframe(open_positions_display, use_container_width=True)

    # Profit/loss analysis - ONLY for the line chart
    st.subheader(T["p_l_analysis"])

    time_options = T["time_display_options"]
    period_translations = T.get("period_translations", {})
    selected_timeframe = st.selectbox(T["period_cumulative_chart"], time_options, key="data_range_label")

    # Filter data based on time frame
    if selected_timeframe == T["last_thirty_days"]:
        cutoff_date = datetime.now() - timedelta(days=30)
        chart_df = df[df['date'] >= cutoff_date]
        chart_title = T["cumulative_p_l_last_30_days"]
    elif selected_timeframe == T["last_365_days"]:
        cutoff_date = datetime.now() - timedelta(days=365)
        chart_df = df[df['date'] >= cutoff_date]
        chart_title = T["cumulative_p_l_last_365_days"]
    else:
        chart_df = df
        chart_title = T["cumulative_p_l_full"]

    # Profit/loss chart
    if not chart_df.empty:
        # Cumulative gain over time
        df_daily = chart_df.groupby('date')['gain'].sum().cumsum().reset_index()

        # Customized X-axis labeling
        date_range_label = get_date_range_label(chart_df, selected_timeframe)

        fig_timeline = px.line(
            df_daily,
            x='date',
            y='gain',
            title=chart_title,
            labels={'gain': T["cumulative_win"], 'date': f'{T["date"]} ({date_range_label})'}
        )
        fig_timeline.update_layout(height=400)
        fig_timeline.update_traces(line_color='#667eea', line_width=3)

        # Improve X-axis formatting
        fig_timeline.update_xaxes(
            title_text=f"{T['date']} ({date_range_label})",
            tickformat='%d.%m.%Y'
        )

        st.plotly_chart(fig_timeline, use_container_width=True)
    else:
        st.info(T["no_data_for_period"])

    # Daily performance calendar with monthly selection
    st.subheader(T["monthly_trading_calendar"])

    # Monthly and annual selection
    col1, col2 = st.columns(2)

    current_date = datetime.now()

    # Month
    with col1:
        months = T["months"]
        selected_month = st.selectbox(f"{T['month']}:", months, index=current_date.month - 1, key="selected_month")
        month_number = months.index(selected_month) + 1

    # Year
    with col2:
        # Determine available years from the data
        available_years = sorted(df['date'].dt.year.unique()) if not df.empty else [current_date.year]
        selected_year = st.selectbox(f"{T['year']}:", available_years, index=len(available_years) - 1, key="selected_year")

    # Create calendar
    calendar_fig = create_monthly_calendar_view(df, selected_year, month_number)
    if calendar_fig:
        st.plotly_chart(calendar_fig, use_container_width=True)
    else:
        st.info(T["no_data_calendar"])

    # Charts in two columns
    col1, col2 = st.columns(2)

    with col1:
        st.subheader(T["performance_by_basis_product"])
        if not df.empty:
            basis_performance = df.groupby('basis_product')['gain'].sum().reset_index()

            fig_basis = px.bar(
                basis_performance,
                x='basis_product',
                y='gain',
                title=T["p_l_by_basis_product"],
                labels={'gain': T["p_l_euro"], 'basis_product': T["base_value"]},
                color='gain',
                color_continuous_scale='RdYlGn'
            )
            fig_basis.update_layout(height=400)
            st.plotly_chart(fig_basis, use_container_width=True)

    with col2:
        st.subheader(T["performace_by_stragey"])
        if not df.empty:
            direction_perf = df.groupby('direction').agg({
                'gain': 'sum',
                'transaction_id': 'count'
            }).reset_index()
            direction_perf.columns = ['direction', 'total_gain', 'trade_count']

            fig_direction = px.bar(
                direction_perf,
                x='direction',
                y='total_gain',
                title=T["p_l_by_strategy"],
                labels={
                    'total_gain': T["total_gain"],
                    'direction': T["strategy"]
                },
                color='total_gain',
                color_continuous_scale='RdYlGn'
            )
            fig_direction.update_layout(height=400)
            st.plotly_chart(fig_direction, use_container_width=True)

    # detailed transaction overview
    st.header(T["transaction_overview"])

    # Top performer
    col1, col2 = st.columns(2)

    column_mapping = T["column_mapping"]
    with col1:
        st.subheader(T["top_performer"])
        top_winners = df.nlargest(5, 'gain')[['date', 'name', 'wkn', 'gain']]
        top_winners['date'] = top_winners['date'].dt.strftime('%d.%m.%Y')
        st.dataframe(top_winners.rename(columns=column_mapping), use_container_width=True)

    with col2:
        st.subheader(T["worst_performer"])
        top_losers = df.nsmallest(5, 'gain')[['date', 'name', 'wkn', 'gain']]
        top_losers['date'] = top_losers['date'].dt.strftime('%d.%m.%Y')
        st.dataframe(top_losers.rename(columns=column_mapping), use_container_width=True)

    # all transactions
    st.subheader(T["all_transactions"])

    display_columns = [
        'date', 'name', 'wkn', 'product_type', 'action', 'qty', 'price', 'total_price', 'gain'
    ]

    display_df = df[display_columns].copy()
    display_df['date'] = display_df['date'].dt.strftime('%d.%m.%Y')
    display_df = display_df.rename(columns=column_mapping)
    st.dataframe(
        display_df.sort_values(T["date"], ascending=False),
        use_container_width=True,
        height=400
    )

if __name__=="__main__":
    main()

