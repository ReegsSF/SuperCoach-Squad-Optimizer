import streamlit as st
import pandas as pd
import subprocess

st.set_page_config(page_title="SuperFantasy Optimizer", layout="centered")

st.title("🧠 SuperFantasy Optimizer")
st.write("Upload your projections CSV and run the optimizer.")

uploaded_file = st.file_uploader("Upload CSV", type=["csv"])

if uploaded_file:
    with open("input.csv", "wb") as f:
        f.write(uploaded_file.getbuffer())

    st.success("File uploaded successfully.")

    if st.button("Run Optimizer"):
        with st.spinner("Running optimizer..."):
            subprocess.run(
                ["python", "optimizer_sc_copy.py"],
                check=True
            )

        st.success("Optimization complete!")

        result = pd.read_csv("AFLSupercoach2026_Squad.csv")
        st.dataframe(result)

        st.download_button(
            label="⬇️ Download Optimized Squad",
            data=result.to_csv(index=False),
            file_name="optimized_squad.csv",
            mime="text/csv"

        )
