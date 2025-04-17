# File: app/ui_components.py
import streamlit as st
import pandas as pd
import altair as alt

def display_risks_chart(risks):
    if risks:
        df = pd.DataFrame({'Risk': risks})
        chart = alt.Chart(df).mark_bar().encode(
            y='Risk:N',
            x='count():Q'
        ).properties(width=700, height=300)
        st.altair_chart(chart)

def display_recommendation_links(recommendations):
    for rec, link in recommendations:
        st.markdown(f"- ✅ [{rec}]({link})")
