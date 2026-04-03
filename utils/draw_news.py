import plotly.graph_objects as go
import streamlit as st


def draw_issue_freq_bar(df_issue_freq, right_issue_chart_height):
    text_raw = "#FFFFFF" if st.session_state.get("theme_mode", "Dark") == "Dark" else "#1F2937"

    try:
        if df_issue_freq.empty:
            st.info("최근 1주일 기준 광물 뉴스 데이터가 없습니다.")
            return

        x_labels = df_issue_freq["mineral_display"].tolist()
        y_values = df_issue_freq["cnt"].tolist()
        colors = ["#D32F2F" if v >= 70 else "#FBC02D" if v >= 40 else "#4CAF50" for v in y_values]
        plot_height = max(180, right_issue_chart_height - 12)

        fig_bar = go.Figure(
            go.Bar(
                x=x_labels,
                y=y_values,
                marker_color=colors,
                text=[int(v) for v in y_values],
                textposition="outside",
                textfont=dict(size=11),
            )
        )

        fig_bar.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            height=plot_height,
            margin=dict(l=8, r=6, t=12, b=8),
            xaxis=dict(tickfont=dict(color=text_raw, size=14)),
            yaxis=dict(
                title=dict(text="뉴스 건수", font=dict(size=11)),
                tickfont=dict(color=text_raw, size=10),
                gridcolor="rgba(255,255,255,0.08)",
            ),
        )

        st.plotly_chart(fig_bar, use_container_width=True)
    except Exception as e:
        st.error(f"광물별 금주 이슈 조회 오류: {e}")
