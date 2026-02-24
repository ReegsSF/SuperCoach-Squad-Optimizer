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

st.title("🟢 AFL SuperCoach Optimizer 🟢")
st.write("Upload your SuperCoach CSV and run the optimizer.")

# -----------------------------
# FILE UPLOAD
# -----------------------------
uploaded_file = st.file_uploader(
    "Upload your input CSV",
    type=["csv"]
)

if uploaded_file is not None:

    with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
        tmp.write(uploaded_file.getbuffer())
        temp_csv_path = tmp.name

    st.success("CSV uploaded successfully")

    if st.button("🚀 Run Optimizer"):

        with st.spinner("Optimizing squad..."):
            try:
                squad = run_optimizer(temp_csv_path)

                st.success("Optimization complete!")

                # -----------------------------
                # ON FIELD
                # -----------------------------
                st.subheader("🏆 ON FIELD")

                on_field = squad[squad["role"] == "On Field"]

                for slot in ["DEF", "MID", "RUC", "FWD", "FLEX"]:
                    st.markdown(f"### {slot}")

                    rows = (
                        on_field[on_field["slot"] == slot]
                        .sort_values("adjusted_avg", ascending=False)
                    )

                    if rows.empty:
                        st.write("_No players_")
                        continue

                    for _, r in rows.iterrows():
                        bonus = f"+{r['elite_bonus']}" if r.get("elite_bonus", 0) > 0 else ""
                        st.write(
                            f"**{r['name']}** ({r['position']}) — "
                            f"${int(r['price']):,} | "
                            f"Adj Avg: {round(r['adjusted_avg'], 1)} {bonus}"
                        )

                # -----------------------------
                # BENCH
                # -----------------------------
                st.subheader("🪑 BENCH")

                bench = squad[squad["role"] == "Bench"]

                for slot in ["DEF", "MID", "RUC", "FWD"]:
                    st.markdown(f"### {slot}")

                    rows = (
                        bench[bench["slot"] == slot]
                        .sort_values("price")
                    )

                    if rows.empty:
                        st.write("_No players_")
                        continue

                    for _, r in rows.iterrows():
                        bonus = f"+{r['elite_bonus']}" if r.get("elite_bonus", 0) > 0 else ""
                        st.write(
                            f"**{r['name']}** ({r['position']}) — "
                            f"${int(r['price']):,} | "
                            f"Adj Avg: {round(r['adjusted_avg'], 1)} {bonus}"
                        )

                # -----------------------------
                # SUMMARY
                # -----------------------------
                st.subheader("📊 SUMMARY")
                st.write(f"**Total Players:** {len(squad)}")
                st.write(f"**Total Price:** ${int(squad['price'].sum()):,}")
                st.write(f"**Total Adjusted Avg:** {round(squad['adjusted_avg'].sum(), 2)}")

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

    os.unlink(temp_csv_path)
