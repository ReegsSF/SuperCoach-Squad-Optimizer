import streamlit as st
import pandas as pd
import tempfile
import os

from optimizer_sc_copy import run_optimizer

# -----------------------------
# PAGE SETUP
# -----------------------------
st.set_page_config(
    page_title="SuperFantasy – AFL SuperCoach Optimizer",
    layout="wide"
)

st.title("🟢 AFL SuperCoach Optimizer 🟢")
st.write("Upload your SuperCoach CSV and run the optimizer.")

# -----------------------------
# FILE UPLOAD
# -----------------------------
uploaded_file = st.file_uploader(
    "Upload your SuperCoach input CSV",
    type=["csv"]
)

if uploaded_file is not None:

    with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
        tmp.write(uploaded_file.getbuffer())
        csv_path = tmp.name

    st.success("CSV uploaded successfully")

    if st.button("🚀 Run Optimizer"):
        with st.spinner("Optimizing squad..."):
            try:
                # -----------------------------
                # RUN OPTIMIZER
                # -----------------------------
                on_field, bench = run_optimizer(csv_path)

                # Reload CSV so we can map player indexes → rows
                df = pd.read_csv(csv_path)
                df = df.loc[:, ~df.columns.str.contains("^Unnamed")]

                st.success("Optimization complete!")

                # -----------------------------
                # ON FIELD DISPLAY
                # -----------------------------
                st.subheader("🏆 ON FIELD")

                for slot in ["DEF", "MID", "RUC", "FWD", "FLEX"]:
                    st.markdown(f"### {slot}")

                    rows = [
                        (p, s) for (p, s) in on_field if s == slot
                    ]

                    if not rows:
                        st.write("_No players_")
                        continue

                    for p, _ in rows:
                        r = df.loc[p]
                        st.write(
                            f"**{r['name']}** ({r['position']}) — "
                            f"${int(r['price']):,} | "
                            f"Adj Avg: {round(r['expected_avg'], 1)}"
                        )

                # -----------------------------
                # BENCH DISPLAY
                # -----------------------------
                st.subheader("🪑 BENCH")

                for slot in ["DEF", "MID", "RUC", "FWD"]:
                    st.markdown(f"### {slot}")

                    rows = [
                        (p, s) for (p, s) in bench if s == slot
                    ]

                    if not rows:
                        st.write("_No players_")
                        continue

                    for p, _ in rows:
                        r = df.loc[p]
                        st.write(
                            f"**{r['name']}** ({r['position']}) — "
                            f"${int(r['price']):,} | "
                            f"Adj Avg: {round(r['expected_avg'], 1)}"
                        )

                # -----------------------------
                # SUMMARY
                # -----------------------------
                st.subheader("📊 SUMMARY")

                selected_players = {p for p, _ in on_field} | {p for p, _ in bench}

                st.write(f"**Total Players:** {len(selected_players)}")
                st.write(
                    f"**Total Price:** ${int(df.loc[list(selected_players), 'price'].sum()):,}"
                )
                st.write(
                    f"**Total Projected Avg:** {round(df.loc[list(selected_players), 'expected_avg'].sum(), 2)}"
                )

                # -----------------------------
                # DOWNLOAD CSV
                # -----------------------------
                squad_df = df.loc[list(selected_players)].copy()

                csv_out = squad_df.to_csv(index=False).encode("utf-8")

                st.download_button(
                    "⬇️ Download Squad CSV",
                    csv_out,
                    file_name="AFLSupercoach2026_Squad.csv",
                    mime="text/csv"
                )

            except Exception as e:
                st.error("Optimizer failed")
                st.exception(e)

    os.unlink(csv_path)
