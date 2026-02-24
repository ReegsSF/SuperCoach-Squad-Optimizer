import streamlit as st
import pandas as pd
import tempfile
import os

from optimizer_sc_copy import run_optimizer

# -----------------------------
# PAGE SETUP
# -----------------------------
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

                # -----------------------------
                # FULL SQUAD TABLE
                # -----------------------------
                st.subheader("📋 Full Optimized Squad")
                st.dataframe(squad, use_container_width=True)

                # -----------------------------
                # ON FIELD
                # -----------------------------
                st.subheader("🏆 ON FIELD")

                for line in ["DEF", "MID", "RUC", "FWD"]:
                    st.markdown(f"### {line}")

                    line_df = (
                        squad[squad["position"].str.contains(line)]
                        .sort_values("adjusted_avg", ascending=False)
                    )

                    for _, r in line_df.iterrows():
                        st.write(
                            f"**{r['name']}** ({r['position']}) — "
                            f"${r['price']:,} | "
                            f"Adj Avg: {round(r['adjusted_avg'], 1)}"
                        )

                # -----------------------------
                # BENCH (CHEAPEST PER LINE)
                # -----------------------------
                st.subheader("🪑 BENCH")

                bench_structure = {
                    "DEF": 2,
                    "MID": 3,
                    "RUC": 1,
                    "FWD": 2
                }

                for line, count in bench_structure.items():
                    st.markdown(f"### {line} Bench")

                    bench_df = (
                        squad[squad["position"].str.contains(line)]
                        .sort_values("price")
                        .head(count)
                    )

                    for _, r in bench_df.iterrows():
                        st.write(
                            f"**{r['name']}** ({r['position']}) — "
                            f"${r['price']:,} | "
                            f"Adj Avg: {round(r['adjusted_avg'], 1)}"
                        )

                # -----------------------------
                # DOWNLOAD CSV
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
