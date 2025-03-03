import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import os
from datetime import datetime

# MCC Codes dictionary
MCC_CODES = {
    '5411': 'Grocery Stores',
    '5542': 'Gas Stations',
    '5812': 'Restaurants',
    '5814': 'Fast Food',
    '5912': 'Drug Stores',
    '5311': 'Department Stores',
    '5699': 'Clothing Stores',
    '7832': 'Movie Theaters',
    '5732': 'Electronics',
    '4899': 'Cable/Internet Services',
}

def show_transactions_tab():
    """Show transaction analysis tab"""
    st.title("Transaction Analysis & Customer Profiling")
    
    # Upload transaction data
    uploaded_file = st.file_uploader(
        "Upload transaction history CSV file",
        type=["csv"],
        help="Upload the CSV file generated by the transaction generator"
    )
    
    if not uploaded_file:
        st.info("Please upload a transaction history file to begin analysis.")
        
        # Explain how to generate the file
        with st.expander("How to generate transaction data"):
            st.write("""
            1. The transaction history file can be generated using the `generate_transactions.py` script
            2. This script creates realistic transaction data for all customers
            3. Once generated, upload the CSV file here for analysis
            """)
        return
    
    # Load transaction data
    transactions_df = pd.read_csv(uploaded_file)
    
    # Basic data cleaning
    if 'transaction_date' in transactions_df.columns:
        transactions_df['transaction_date'] = pd.to_datetime(transactions_df['transaction_date'])
    
    if 'transaction_amount' in transactions_df.columns:
        transactions_df['transaction_amount'] = pd.to_numeric(transactions_df['transaction_amount'], errors='coerce')
    
    # Show data overview
    st.subheader("Transaction Data Overview")
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    col1.metric("Total Transactions", f"{len(transactions_df):,}")
    col2.metric("Total Customers", f"{transactions_df['customer_id'].nunique():,}")
    col3.metric("Total Spend", f"${transactions_df['transaction_amount'].sum():,.2f}")
    col4.metric("Avg Transaction", f"${transactions_df['transaction_amount'].mean():.2f}")
    
    # Create tabs for different analysis views
    tab1, tab2, tab3 = st.tabs([
        "👤 Customer Analysis", 
        "📈 Transaction Trends", 
        "🏪 Merchant Analysis"
    ])
    
    with tab1:
        st.subheader("Customer Spending Analysis")
        
        # Select customer for analysis
        # Customer selector - handle case when customer_name is not available
        if 'customer_name' in transactions_df.columns:
            # Create list of (id, name) tuples
            customer_list = []
            for cid in transactions_df['customer_id'].unique():
                name = transactions_df[transactions_df['customer_id'] == cid]['customer_name'].iloc[0]
                customer_list.append((cid, name))
            
            # Sort by name
            customer_list = sorted(customer_list, key=lambda x: x[1])
            
            selected_customer = st.selectbox(
                "Select Customer",
                options=[id for id, _ in customer_list],
                format_func=lambda id: next((name for cid, name in customer_list if cid == id), id)
            )
        else:
            # Just use IDs if names aren't available
            customer_ids = sorted(transactions_df['customer_id'].unique())
            selected_customer = st.selectbox(
                "Select Customer",
                options=customer_ids
            )
        
        # Filter for selected customer
        customer_data = transactions_df[transactions_df['customer_id'] == selected_customer]
        
        if not customer_data.empty:
            # Get customer name if available, otherwise use ID
            customer_name = customer_data['customer_name'].iloc[0] if 'customer_name' in customer_data.columns else selected_customer
            
            # Customer metrics
            st.subheader(f"Spending Profile: {customer_name}")
            
            cust_col1, cust_col2, cust_col3 = st.columns(3)
            
            total_spend = customer_data['transaction_amount'].sum()
            cust_col1.metric("Total Spend", f"${total_spend:.2f}")
            
            txn_count = len(customer_data)
            cust_col2.metric("Transaction Count", f"{txn_count}")
            
            avg_txn = total_spend / txn_count if txn_count > 0 else 0
            cust_col3.metric("Avg Transaction", f"${avg_txn:.2f}")
            
            # Category breakdown
            st.subheader("Spending by Category")
            
            # Group by category
            category_spend = customer_data.groupby('merchant_category_code').agg({
                'transaction_amount': 'sum',
                'transaction_id': 'count'
            }).reset_index()
            
            # Add category names
            category_spend['category_name'] = category_spend['merchant_category_code'].map(
                lambda x: MCC_CODES.get(x, 'Unknown')
            )
            
            # Calculate percentages
            category_spend['spend_percentage'] = category_spend['transaction_amount'] / total_spend * 100
            
            # Sort by spend
            category_spend = category_spend.sort_values('transaction_amount', ascending=False)
            
            # Display as chart
            fig = px.pie(
                category_spend, 
                values='transaction_amount', 
                names='category_name',
                title="Spending by Category"
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Merchant breakdown
            st.subheader("Top Merchants")
            
            # Group by merchant
            merchant_spend = customer_data.groupby('merchant_name').agg({
                'transaction_amount': 'sum',
                'transaction_id': 'count'
            }).reset_index()
            
            # Sort by spend
            merchant_spend = merchant_spend.sort_values('transaction_amount', ascending=False)
            
            # Display as bar chart
            fig = px.bar(
                merchant_spend.head(10),
                x='merchant_name',
                y='transaction_amount',
                title="Top 10 Merchants by Spend",
                labels={'transaction_amount': 'Total Spend', 'merchant_name': 'Merchant'}
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Behavioral insights
            st.subheader("Behavioral Insights")
            
            # Primary interests (top categories)
            primary_interests = category_spend[category_spend['spend_percentage'] >= 15]
            
            if not primary_interests.empty:
                st.write("**Primary Interests:**")
                for _, row in primary_interests.iterrows():
                    st.write(f"- {row['category_name']} ({row['spend_percentage']:.1f}%)")
            
            # Favorite merchants (visited at least 3 times)
            favorite_merchants = merchant_spend[merchant_spend['transaction_id'] >= 3]
            
            if not favorite_merchants.empty:
                st.write("**Favorite Merchants:**")
                for _, row in favorite_merchants.head(5).iterrows():
                    st.write(f"- {row['merchant_name']} ({row['transaction_id']} visits)")
            
            # Offer recommendations
            st.subheader("Personalized Offer Recommendations")
            
            # Generate simple recommendations based on category preferences
            for _, row in primary_interests.head(3).iterrows():
                category = row['category_name']
                if 'Grocery' in category:
                    st.write("- 5% cashback on grocery purchases")
                elif 'Gas' in category:
                    st.write("- $0.10 off per gallon at partner gas stations")
                elif 'Restaurant' in category or 'Food' in category:
                    st.write("- Buy one get one free at select restaurants")
                elif 'Department' in category:
                    st.write("- 15% off your next department store purchase")
                elif 'Electronics' in category:
                    st.write("- Extended warranty on electronics purchases")
                elif 'Clothing' in category:
                    st.write("- 20% off your next clothing purchase")
                else:
                    st.write(f"- Special offers on {category}")
        else:
            st.warning(f"No transaction data found for {selected_customer}")
    
    with tab2:
        st.subheader("Transaction Trends")
        
        # Daily transaction volume
        st.write("**Daily Transaction Volume**")
        
        daily_txns = transactions_df.groupby(transactions_df['transaction_date'].dt.date).agg({
            'transaction_id': 'count',
            'transaction_amount': 'sum'
        }).reset_index()
        
        # Display chart
        fig = px.line(
            daily_txns,
            x='transaction_date',
            y='transaction_id',
            title="Daily Transaction Count"
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Daily spending
        st.write("**Daily Spending**")
        
        fig = px.line(
            daily_txns,
            x='transaction_date',
            y='transaction_amount',
            title="Daily Transaction Amount"
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Transactions by day of week
        st.write("**Transactions by Day of Week**")
        
        transactions_df['day_of_week'] = transactions_df['transaction_date'].dt.day_name()
        
        # Order days correctly
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        dow_txns = transactions_df.groupby('day_of_week').agg({
            'transaction_id': 'count',
            'transaction_amount': 'sum'
        }).reset_index()
        
        # Sort by day of week
        dow_txns['day_num'] = dow_txns['day_of_week'].map({day: i for i, day in enumerate(day_order)})
        dow_txns = dow_txns.sort_values('day_num')
        
        # Display chart
        fig = px.bar(
            dow_txns,
            x='day_of_week',
            y='transaction_id',
            title="Transaction Count by Day of Week",
            category_orders={"day_of_week": day_order}
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        st.subheader("Merchant and Category Analysis")
        
        # Spending by category
        st.write("**Spending by Merchant Category**")
        
        category_totals = transactions_df.groupby('merchant_category_code').agg({
            'transaction_amount': 'sum',
            'transaction_id': 'count',
            'customer_id': pd.Series.nunique
        }).reset_index()
        
        # Add category names
        category_totals['category_name'] = category_totals['merchant_category_code'].map(
            lambda x: MCC_CODES.get(x, 'Unknown')
        )
        
        # Sort by spend
        category_totals = category_totals.sort_values('transaction_amount', ascending=False)
        
        # Display chart
        fig = px.bar(
            category_totals,
            x='category_name',
            y='transaction_amount',
            title="Total Spend by Category"
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Top merchants
        st.write("**Top Merchants by Spend**")
        
        merchant_totals = transactions_df.groupby('merchant_name').agg({
            'transaction_amount': 'sum',
            'transaction_id': 'count',
            'customer_id': pd.Series.nunique
        }).reset_index()
        
        # Sort by spend
        merchant_totals = merchant_totals.sort_values('transaction_amount', ascending=False)
        
        # Display chart
        fig = px.bar(
            merchant_totals.head(10),
            x='merchant_name',
            y='transaction_amount',
            title="Top 10 Merchants by Spend"
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Merchant popularity
        st.write("**Most Popular Merchants by Customer Count**")
        
        # Sort by customer count
        merchant_by_customers = merchant_totals.sort_values('customer_id', ascending=False)
        
        # Display chart
        fig = px.bar(
            merchant_by_customers.head(10),
            x='merchant_name',
            y='customer_id',
            title="Top 10 Merchants by Unique Customers"
        )
        st.plotly_chart(fig, use_container_width=True)
