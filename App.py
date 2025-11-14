import streamlit as st
import pandas as pd
import plotly.express as px

# -------------------------------
# PAGE CONFIG
# -------------------------------
st.set_page_config(page_title="CloudMart Multi-Account Dashboard", layout="wide")
st.title("☁️ CloudMart Multi-Account Cost & Tagging Analysis")

# -------------------------------
# LOAD CSV FROM LOCAL PATH (CORRECTED)
# -------------------------------
# NOTE: Update this path if you run the app from a different location.
csv_path = r"cloudmart_multi_account.csv"

# --- FIX FOR NON-STANDARD CSV FORMAT AND DATA TYPING ---
try:
    df_single_col = pd.read_csv(csv_path)

    # 1. Get the single column name string
    header_string = df_single_col.columns[0]
    
    # 2. Split the string by comma and apply cleaning
    cleaned_header_list = [col.strip().replace("\ufeff","") for col in header_string.split(',')]
    
    # 3. Split the single data column into a new DataFrame
    df = df_single_col.iloc[:, 0].str.split(',', expand=True)
    df.columns = cleaned_header_list
    
    # 4. Replace empty strings with NaN for proper missing value analysis
    df = df.replace(r'^\s*$', float('nan'), regex=True)

    # 5. Convert 'MonthlyCostUSD' to numeric (Crucial for correct editing in Task 5)
    df['MonthlyCostUSD'] = pd.to_numeric(df['MonthlyCostUSD'])
    
    st.success("✅ CSV loaded and columns successfully parsed!")
    st.write("Columns detected:", df.columns.tolist())

except Exception as e:
    st.error(f"Error loading or parsing CSV. Check path and file format: {e}")
    df = pd.DataFrame() # Use empty DataFrame to prevent downstream errors

# ----------------------------------------------------------------------------------


# -------------------------------
# TASK 1 — DATA EXPLORATION
# -------------------------------
st.header("📊 Task Set 1 — Data Exploration")
if not df.empty:
    st.subheader("1.1 First 5 Rows")
    st.dataframe(df.head())

    st.subheader("1.2 Missing Values per Column")
    st.write(df.isnull().sum())

    st.subheader("1.3 Columns With Most Missing Values")
    st.write(df.isnull().sum().sort_values(ascending=False).head(5))

    st.subheader("1.4 Count of Tagged vs Untagged Resources")
    if "Tagged" in df.columns:
        st.write(df["Tagged"].value_counts(dropna=False))
    else:
        st.warning("Column 'Tagged' not found")

    st.subheader("1.5 Percentage of Untagged Resources")
    if "Tagged" in df.columns and "No" in df["Tagged"].values:
        pct_untagged = (df[df["Tagged"] == "No"].shape[0] / df.shape[0]) * 100
        st.write(f"🔸 {pct_untagged:.2f}% of resources are untagged")


# -------------------------------
# TASK 2 — COST VISIBILITY
# -------------------------------
st.header("💰 Task Set 2 — Cost Visibility")
if not df.empty and all(col in df.columns for col in ["Tagged", "MonthlyCostUSD"]):
    st.subheader("2.1 Total Cost: Tagged vs Untagged")
    st.write(df.groupby("Tagged")["MonthlyCostUSD"].sum())

    st.subheader("2.2 Percentage of Total Cost That is Untagged")
    total_cost = df["MonthlyCostUSD"].sum()
    untagged_cost = df[df["Tagged"] == "No"]["MonthlyCostUSD"].sum()
    
    if total_cost > 0:
        st.write(f"🔸 {untagged_cost / total_cost * 100:.2f}% of monthly cost is untagged")

if not df.empty and all(col in df.columns for col in ["Department", "MonthlyCostUSD", "Tagged"]):
    st.subheader("2.3 Department With Most Untagged Cost")
    dept_untagged = df[df["Tagged"] == "No"].groupby("Department")["MonthlyCostUSD"].sum()
    st.write(dept_untagged.sort_values(ascending=False))

if not df.empty and all(col in df.columns for col in ["Project", "MonthlyCostUSD"]):
    st.subheader("2.4 Project With Highest Total Cost")
    st.write(df.groupby("Project")["MonthlyCostUSD"].sum().sort_values(ascending=False).head(5))

if not df.empty and all(col in df.columns for col in ["Environment", "MonthlyCostUSD", "Tagged"]):
    st.subheader("2.5 Prod vs Dev Cost Comparison")
    st.write(df.groupby(["Environment", "Tagged"])["MonthlyCostUSD"].sum())


# -------------------------------
# TASK 3 — TAGGING COMPLIANCE
# -------------------------------
st.header("🏷️ Task Set 3 — Tagging Compliance")
tag_fields = [col for col in ["Department","Project","Environment","Owner","CostCenter","CreatedBy"] if col in df.columns]

if not df.empty and tag_fields:
    # Calculate completeness score based on the number of non-null tag fields
    df["CompletenessScore"] = df[tag_fields].notnull().sum(axis=1)

    st.subheader("3.1 Tag Completeness Score Per Resource")
    st.write(df[["ResourceID","CompletenessScore"]].head())

    st.subheader("3.2 Top 5 Resources With Lowest Completeness Score")
    st.write(df.sort_values("CompletenessScore").head(5))

    st.subheader("3.3 Most Frequently Missing Tag Fields")
    st.write(df[tag_fields].isnull().sum().sort_values(ascending=False))
    
    # --- TASK 3.4/3.5: Filter for ALL incomplete resources ---
    st.subheader("3.4 Incomplete Resources")
    
    # Create a mask: True if ANY of the required tag columns is NaN/missing.
    incomplete_mask = df[tag_fields].isnull().any(axis=1)
    
    # Filter the DataFrame for incomplete rows and fill NaN for clean display in this section
    incomplete_df = df[incomplete_mask].fillna('') 
    
    # Define 'untagged_df' to be used in the Download button
    untagged_df = incomplete_df
    
    st.dataframe(untagged_df)
    
    st.subheader("3.5 Download Incomplete Resources CSV")
    if not untagged_df.empty:
        st.download_button("⬇️ Download Incomplete Resources", untagged_df.to_csv(index=False), "incomplete_resources.csv")
else:
    untagged_df = pd.DataFrame()
    st.warning("No tag columns found to calculate CompletenessScore.")


# -------------------------------
# TASK 4 — VISUALIZATION DASHBOARD
# -------------------------------
st.header("📈 Task Set 4 — Visualization Dashboard")

filtered = df.copy()

# Add filters only if columns exist
if "Service" in df.columns:
    service_filter = st.multiselect("Filter by Service", df["Service"].dropna().unique())
    if service_filter: filtered = filtered[filtered["Service"].isin(service_filter)]

if "Region" in df.columns:
    region_filter = st.multiselect("Filter by Region", df["Region"].dropna().unique())
    if region_filter: filtered = filtered[filtered["Region"].isin(region_filter)]

if "Department" in df.columns:
    dept_filter = st.multiselect("Filter by Department", df["Department"].dropna().unique())
    if dept_filter: filtered = filtered[filtered["Department"].isin(dept_filter)]

if not filtered.empty:
    # 4.1 Pie chart: Tagged vs Untagged
    st.subheader("4.1 Tagged vs Untagged Resources")
    if "Tagged" in df.columns:
        # Drop rows where 'Tagged' status itself is missing for plotting clarity
        fig1 = px.pie(filtered.dropna(subset=['Tagged']), names="Tagged", title="Tag Compliance")
        st.plotly_chart(fig1, use_container_width=True)

    # 4.2 Bar chart: Cost per Department by Tag
    st.subheader("4.2 Cost per Department (Tagged vs Untagged)")
    if all(col in df.columns for col in ["Department", "MonthlyCostUSD", "Tagged"]):
        dept_cost = filtered.groupby(["Department","Tagged"])["MonthlyCostUSD"].sum().reset_index()
        fig2 = px.bar(dept_cost, x="Department", y="MonthlyCostUSD", color="Tagged", barmode="group",
                      title="Total Monthly Cost by Department and Tag Status")
        st.plotly_chart(fig2, use_container_width=True)

    # 4.3 Horizontal bar: Total cost per Service
    st.subheader("4.3 Total Cost per Service")
    if all(col in df.columns for col in ["Service", "MonthlyCostUSD"]):
        service_cost = filtered.groupby("Service")["MonthlyCostUSD"].sum().sort_values().reset_index()
        fig3 = px.bar(service_cost, x="MonthlyCostUSD", y="Service", orientation="h",
                      title="Total Monthly Cost by Service")
        st.plotly_chart(fig3, use_container_width=True)

    # 4.4 Cost by Environment
    st.subheader("4.4 Cost by Environment")
    if all(col in df.columns for col in ["Environment", "MonthlyCostUSD"]):
        env_cost = filtered.groupby("Environment")["MonthlyCostUSD"].sum().reset_index()
        fig4 = px.bar(env_cost, x="Environment", y="MonthlyCostUSD", color="Environment",
                      title="Total Monthly Cost by Environment")
        st.plotly_chart(fig4, use_container_width=True)


# -------------------------------
# TASK 5 — TAG REMEDIATION WORKFLOW
# -------------------------------
st.header("🛠️ Task Set 5 — Tag Remediation Workflow")
st.subheader("Editable Table for All Resources") # TITLE CHANGED
if not df.empty:
    # --- CHANGE: Using the main DataFrame 'df' which preserves the float type for editing ---
    edited_table = st.data_editor(df, num_rows="dynamic")
    # -------------------------------------------------------------------------------------
    st.download_button("⬇️ Download Updated Data", edited_table.to_csv(index=False), "updated_data.csv")
else:
    st.info("Data is empty.")