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

                # -----------------------------
                # ENSURE PRIMARY POSITION
                # -----------------------------
                def primary_position(pos_str):
                    pos_list = pos_str.split("|")
                    if "RUC" in pos_list:
                        return "RUC"
                    if "FWD" in pos_list:
                        return "FWD"
                    if "DEF" in pos_list:
                        return "DEF"
                    return "MID"

                squad["primary_pos"] = squad["position"].apply(primary_position)

                # Sort once by adjusted avg (descending)
                squad = squad.sort_values("adjusted_avg", ascending=False)

                # -----------------------------
                # ON FIELD SELECTION
                # -----------------------------
                on_field_structure = {
                    "DEF": 6,
                    "MID": 8,
                    "RUC": 2,
                    "FWD": 6,
                }

                on_field_rows = []
                remaining = squad.copy()

                for pos, count in on_field_structure.items():
                    selected = remaining[remaining["primary_pos"] == pos].head(count)
                    on_field_rows.append(selected)
                    remaining = remaining.drop(selected.index)

                # FLEX (best remaining player)
                flex = remaining.head(1)
                on_field_rows.append(flex)
                remaining = remaining.drop(flex.index)

                on_field_df = pd.concat(on_field_rows)

                # -----------------------------
                # BENCH SELECTION (FROM REMAINING ONLY)
                # -----------------------------
                bench_structure = {
                    "DEF": 2,
                    "MID": 3,
                    "RUC": 1,
                    "FWD": 2
                }

                bench_rows = []

                for pos, count in bench_structure.items():
                    selected = (
                        remaining[remaining["primary_pos"] == pos]
                        .sort_values("price")
                        .head(count)
                    )
                    bench_rows.append(selected)
                    remaining = remaining.drop(selected.index)

                bench_df = pd.concat(bench_rows)

                # -----------------------------
                # DISPLAY
                # -----------------------------
                st.success("Optimization complete!")

                st.subheader("🏆 ON FIELD")
                for pos in ["DEF", "MID", "RUC", "FWD", "FLEX"]:
                    st.markdown(f"### {pos}")

                    if pos == "FLEX":
                        rows = on_field_df.loc[flex.index]
                    else:
                        rows = on_field_df[on_field_df["primary_pos"] == pos]

                    for _, r in rows.iterrows():
                        bonus = f"+{r['elite_bonus']}" if r["elite_bonus"] > 0 else ""
                        st.write(
                            f"**{r['name']}** ({r['position']}) — "
                            f"${r['price']:,} | "
                            f"Adj Avg: {round(r['adjusted_avg'], 1)} {bonus}"
                        )

                st.subheader("🪑 BENCH")
                for pos in ["DEF", "MID", "RUC", "FWD"]:
                    st.markdown(f"### {pos}")

                    rows = bench_df[bench_df["primary_pos"] == pos]

                    for _, r in rows.iterrows():
                        bonus = f"+{r['elite_bonus']}" if r["elite_bonus"] > 0 else ""
                        st.write(
                            f"**{r['name']}** ({r['position']}) — "
                            f"${r['price']:,} | "
                            f"Adj Avg: {round(r['adjusted_avg'], 1)} {bonus}"
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

    os.unlink(temp_csv_path)
