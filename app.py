import streamlit as st
import pandas as pd
from datetime import datetime
import pyarrow as pa
import pyarrow.parquet as pq

# Load data
EXCEL_PATH = "Case List_Test.xlsx"
SHEET_NAME = "RawData"

@st.cache_data
def load_data():
    return pd.read_excel(EXCEL_PATH, sheet_name=SHEET_NAME)

def save_data(df):
    # Save a backup version in Parquet just for versioning purposes
    table = pa.Table.from_pandas(df)
    pq.write_table(table, "RawData_backup.parquet")
    df.to_excel(EXCEL_PATH, sheet_name=SHEET_NAME, index=False)

df = load_data()

# Streamlit UI
st.title("🎯 QA Assignment App")
st.write("Automatically assign 1 unchecked case to a QA Specialist.")

# Select QA Specialist
qa_names = df['QA Specialaist'].dropna().unique()
selected_qa = st.selectbox("Select your name (QA Specialist)", qa_names)

if selected_qa:
    # Get all agents this QA is responsible for
    assigned_agents = df[df['QA Specialaist'] == selected_qa]['Employee Name'].unique()
    month_now = datetime.now().strftime("%B")

    # Filter unchecked cases this QA is allowed to assign
    available_cases = df[
        (df['QA Specialaist'] == selected_qa) &
        (df['Status'].isna()) &
        (df['Month'] == month_now)
    ]

    # Count how many cases are already checked per agent
    checked_cases = df[
        (df['QA Specialaist'] == selected_qa) &
        (df['Status'] == 'Checked') &
        (df['Month'] == month_now)
    ]['Employee Name'].value_counts().to_dict()

    # Find eligible agent with <5 checks
    eligible_case = None
    for _, row in available_cases.iterrows():
        agent = row['Employee Name']
        if checked_cases.get(agent, 0) < 5:
            eligible_case = row
            break

    if eligible_case is not None:
        st.success("✅ Case found and assigned!")
        st.write(eligible_case)

        # Update the dataframe with this assignment (but only if "Confirm" is clicked)
        if st.button("Confirm assignment"):
            idx = df.index[(df['Case ID'] == eligible_case['Case ID'])].tolist()[0]
            df.at[idx, 'Status'] = 'Checked'
            df.at[idx, 'Checked On'] = datetime.now().strftime("%Y-%m-%d")
            save_data(df)
            st.success("🎉 Case marked as checked!")
    else:
        st.warning("All agents already have 5 checked cases for this month.")
