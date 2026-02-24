import streamlit as st
import pandas as pd
import tempfile
import os

from optimizer_sc_copy import run_optimizer

st.set_page_config(
    page_title="SuperFantasy Optimizer",
    layout="wide"
)

st.title("🔥 AFL SuperCoach Optimizer")
st.write("Upload your SuperCoach CSV and run the optimizer.")

# -----------------------------
# FILE UPLOAD
# -----------------------------
uploaded_file = st.file_uploader(
    "Upload your input CSV",
    type=["csv"]
)

if uploaded_file is not None:

    # Save uploaded CSV to a temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
        tmp.write(uploaded_file.getbuffer())
        temp_csv_path = tmp.name

    st.success("CSV uploaded successfully")

    # -----------------------------
    # RUN OPTIMIZER
    # -----------------------------
    if st.button("🚀 Run Optimizer"):

        with st.spinner("Optimizing squad..."):
            try:
                squad = run_optimizer(temp_csv_path)

                st.success("Optimization complete!")

                st.subheader("📋 Optimized Squad")
                st.dataframe(squad)

                # -----------------------------
                # DOWNLOAD OUTPUT
                # -----------------------------
                csv_out = squad.to_csv(index=False).encode("utf-8")

                st.download_button(
                    "⬇️ Download Squad CSV",
                    csv_out,
                    file_name="AFLSupercoach2026_Squad.csv",
                    mime="text/csv"
                )

            except Exception as e:
                st.error("Optimizer failed")
                st.exception(e)

    # Cleanup temp file
    os.unlink(temp_csv_path)
