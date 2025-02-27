import streamlit as st
import sys
import pandas as pd
import random
import datetime
import uuid
import os
import time

# Check if Faker is installed
try:
    from faker import Faker
    fake = Faker()
except ImportError:
    st.error("Faker library is not installed. Please add it to requirements.txt")
    fake = None

st.title("Transaction History Generator")
st.write("This tool generates transaction history data for your customers")

if fake is None:
    st.stop()

# Import generation script
try:
    import generate_transaction_csv
    st.success("Transaction generator loaded successfully")
except ImportError:
    st.error("Could not import generate_transaction_csv.py")
    st.stop()

if st.button("Generate Transaction History"):
    with st.spinner("Generating transaction data... This may take a minute or two."):
        try:
            # Run the main function
            generate_transaction_csv.main()
            
            # Load the generated file
            file_path = 'customer_transaction_history.csv'
            
            if os.path.exists(file_path):
                # Read the file
                df = pd.read_csv(file_path)
                
                # Show success message
                st.success(f"Generated {len(df)} transactions for {df['customer_id'].nunique()} customers!")
                
                # Show preview
                st.write("Preview of generated data:")
                st.dataframe(df.head())
                
                # Create download button
                csv = df.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name="customer_transaction_history.csv",
                    mime="text/csv"
                )
            else:
                st.error("File generation failed. Could not find the output file.")
        except Exception as e:
            st.error(f"An error occurred: {e}")
