import streamlit as st
import pandas as pd
import numpy as np
import os
import json
from datetime import datetime

# MCC Codes dictionary
MCC_CODES = {
    '5411': 'Grocery Stores',
    '5542': 'Gas Stations',
    '5812': 'Restaurants',
    '5814': 'Fast Food',
    '5912': 'Drug Stores',
    '5311': 'Department Stores',
    '5661': 'Shoe Stores',
    '5699': 'Clothing Stores',
    '7832': 'Movie Theaters',
    '5999': 'Miscellaneous Retail',
    '4111': 'Transportation',
    '7011': 'Hotels',
    '4121': 'Taxis/Rideshares',
    '5732': 'Electronics',
    '8011': 'Medical Services',
    '8021': 'Dental Services',
    '8099': 'Health Services',
    '8299': 'Educational Services',
    '4816': 'Online Services',
    '5945': 'Hobby/Toy Stores',
    '5941': 'Sporting Goods',
    '7999': 'Recreation Services',
    '7230': 'Beauty/Barber Shops',
    '7512': 'Car Rentals',
    '4899': 'Cable/Internet Services',
    '6300': 'Insurance',
}

def load_transactions_data(uploaded_file):
    """Load transaction data from an uploaded file"""
    file_extension = os.path.splitext(uploaded_file.name)[1].lower()
    
    if file_extension == '.csv':
        return pd.read_csv(uploaded_file)
    elif file_extension in ['.xls', '.xlsx']:
        return pd.read_excel(uploaded_file)
    else:
        st.error(f"Unsupported file format: {file_extension}. Please upload a CSV or Excel file.")
        return None

def prepare_transactions_data(df):
    """Clean and prepare transaction data"""
    # Convert date columns to datetime
    if 'transaction_date' in df.columns:
        df['transaction_date'] = pd.to_datetime(df['transaction_date'])
    
    # Ensure numeric columns are properly typed
    numeric_cols = ['transaction_amount', 'fees', 'net_amount']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Filter to approved sales transactions for most analyses
    sales_df = df[(df['transaction_type'] == 'Sale') & (df['transaction_status'] == 'Approved')].copy()
    
    return df, sales_df

def analyze_customer_behavior(sales_df, customer_id):
    """Analyze spending behavior for a specific customer"""
    # Filter to customer transactions
    customer_txns = sales_df[sales_df['customer_id'] == customer_id].copy()
    
    if customer_txns.empty:
        return None
    
    # Get customer name
    customer_name = customer_txns['customer_name'].iloc[0]
    
    # Basic statistics
    total_spend = customer_txns['transaction_amount'].sum()
    avg_transaction = customer_txns['transaction_amount'].mean()
    transaction_count = len(customer_txns)
    
    # Category preferences
    category_spend = customer_txns.groupby('merchant_category_code').agg({
        'transaction_amount': 'sum',
        'transaction_id': 'count'
    }).reset_index()
    
    # Add category names
    category_spend['category_name'] = category_spend['merchant_category_code'].map(
        lambda x: MCC_CODES.get(x, 'Unknown')
    )
    
    # Calculate percentages
    category_spend['spend_percentage'] = category_spend['transaction_amount'] / total_spend * 100
    
    # Get top categories
    top_categories = category_spend.sort_values('spend_percentage', ascending=False)
    
    # Favorite merchants
    merchant_spend = customer_txns.groupby('merchant_name').agg({
        'transaction_amount': 'sum',
        'transaction_id': 'count'
    }).reset_index()
    
    merchant_spend['spend_percentage'] = merchant_spend['transaction_amount'] / total_spend * 100
    top_merchants = merchant_spend.sort_values('spend_percentage', ascending=False)
    
    # Create behavior summary
    behavior_summary = {
        'customer_id': customer_id,
        'customer_name': customer_name,
        'total_spend': total_spend,
        'avg_transaction': avg_transaction,
        'transaction_count': transaction_count,
        'top_categories': top_categories,
        'top_merchants': top_merchants
    }
    
    return behavior_summary

def show_transactions_tab():
    """Show the transaction analysis tab in the Streamlit app"""
    st.title("Transaction Analysis & Customer Profiling")
    
    # Section for uploading transactions
    st.subheader("Upload Transaction Data")
    
    uploaded_file = st.file_uploader(
        "Upload your transaction history CSV or Excel file",
        type=["csv", "xls", "xlsx"],
        key="transaction_file_uploader"
    )
    
    if not uploaded_file:
        st.info("Please upload a transaction history file to begin analysis. The file should include transaction details for all customers.")
        return
    
    # Load and prepare data
    transactions_df = load_transactions_data(uploaded_file)
    
    if transactions_df is None or transactions_df.empty:
        st.error("Could not load transaction data. Please check the file format.")
        return
    
    # Clean and prepare data
    transactions_df, sales_df = prepare_transactions_data(transactions_df)
    
    # Show basic stats
    st.subheader("Transaction Data Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    total_transactions = len(transactions_df)
    total_customers = transactions_df['customer_id'].nunique()
    total_spend = sales_df['transaction_amount'].sum()
    avg_transaction = sales_df['transaction_amount'].mean()
    
    col1.metric("Total Transactions", f"{total_transactions:,}")
    col2.metric("Total Customers", f"{total_customers:,}")
    col3.metric("Total Sales", f"${total_spend:,.2f}")
    col4.metric("Avg Transaction", f"${avg_transaction:.2f}")
    
    # Create tabs for different analysis views
    tab1, tab2 = st.tabs([
        "👥 Customer Profiles", 
        "📊 Transaction Analysis"
    ])
    
    with tab1:
        st.subheader("Customer Behavioral Profiles")
        st.write("Select a customer to view their detailed behavioral profile based on transaction history.")
        
        # Customer selector
        customer_ids = sorted(transactions_df['customer_id'].unique())
        customer_names = {}
        
        for cid in customer_ids:
            name = transactions_df[transactions_df['customer_id'] == cid]['customer_name'].iloc[0]
            customer_names[cid] = name
        
        selected_customer = st.selectbox(
            "Select Customer",
            options=customer_ids,
            format_func=lambda cid: f"{customer_names.get(cid, 'Unknown')} ({cid})"
        )
        
        if selected_customer:
            # Analyze customer behavior
            behavior = analyze_customer_behavior(sales_df, selected_customer)
            
            if behavior:
                # Display customer profile
                st.subheader(f"Profile for {behavior['customer_name']}")
                
                # Key metrics
                col1, col2, col3 = st.columns(3)
                col1.metric("Total Spend", f"${behavior['total_spend']:.2f}")
                col2.metric("Transactions", str(behavior['transaction_count']))
                col3.metric("Avg Transaction", f"${behavior['avg_transaction']:.2f}")
                
                # Category preferences
                st.subheader("Spending by Category")
                
                if not behavior['top_categories'].empty:
                    st.bar_chart(
                        behavior['top_categories'].set_index('category_name')['transaction_amount']
                    )
                    
                    st.write("**Primary Interests:**")
                    primary_interests = behavior['top_categories'][behavior['top_categories']['spend_percentage'] >= 15]
                    if not primary_interests.empty:
                        for i, row in primary_interests.iterrows():
                            st.write(f"- {row['category_name']} ({row['spend_percentage']:.1f}%)")
                    else:
                        st.write("- No strong primary interests identified")
                else:
                    st.write("No category data available")
                
                # Merchant preferences
                st.subheader("Top Merchants")
                
                if not behavior['top_merchants'].empty:
                    st.dataframe(
                        behavior['top_merchants'][['merchant_name', 'transaction_amount', 'transaction_id']].head(10).rename(
                            columns={'transaction_amount': 'Total Spend', 'transaction_id': 'Visit Count'}
                        )
                    )
                    
                    st.write("**Favorite Merchants:**")
                    favorite_merchants = behavior['top_merchants'][
                        (behavior['top_merchants']['transaction_id'] >= 3) | 
                        (behavior['top_merchants']['spend_percentage'] >= 10)
                    ]
                    
                    if not favorite_merchants.empty:
                        for i, row in favorite_merchants.head(5).iterrows():
                            st.write(f"- {row['merchant_name']} ({row['transaction_id']} visits)")
                    else:
                        st.write("- No clear favorite merchants identified")
                else:
                    st.write("No merchant data available")
                
                # Recommended Offers
                st.subheader("Offer Targeting Recommendations")
                
                # Based on top categories
                st.write("**Recommended Offer Types:**")
                
                recommendations = []
                
                for i, row in behavior['top_categories'].head(3).iterrows():
                    category = row['category_name']
                    if 'Grocery' in category:
                        recommendations.append("Cashback offers for grocery stores")
                    elif 'Gas' in category:
                        recommendations.append("Fuel discounts or loyalty programs")
                    elif 'Restaurant' in category or 'Food' in category:
                        recommendations.append("Dining discounts or rewards")
                    elif 'Retail' in category or 'Store' in category:
                        recommendations.append("Retail loyalty program or BOGO offers")
                    elif 'Electronics' in category:
                        recommendations.append("Extended warranty offers or tech bundles")
                    elif 'Online' in category:
                        recommendations.append("Online purchase discounts or free shipping")
                    elif 'Hotel' in category or 'Travel' in category:
                        recommendations.append("Travel packages or hotel discounts")
                    elif 'Health' in category:
                        recommendations.append("Health and wellness product discounts")
                
                # Add general recommendations
                if len(recommendations) < 3:
                    general_recs = [
                        "Personalized discounts at favorite merchants",
                        "Category-specific cashback offers",
                        "Bundle deals for frequently purchased items",
                        "Limited-time promotional offers for new products"
                    ]
                    recommendations.extend(general_recs[:3 - len(recommendations)])
                
                # Display recommendations
                for rec in recommendations[:3]:
                    st.write(f"- {rec}")
            else:
                st.warning(f"No transaction data found for customer {selected_customer}")
    
    with tab2:
        st.subheader("Transaction Insights")
        st.write("Explore patterns and trends in the transaction data.")
        
        # Transaction timeline
        st.write("**Transaction Timeline**")
        
        # Convert transaction_date to datetime and group by date
        transactions_df['transaction_date'] = pd.to_datetime(transactions_df['transaction_date'])
        daily_transactions = transactions_df.groupby(transactions_df['transaction_date'].dt.date).agg({
            'transaction_id': 'count',
            'transaction_amount': 'sum'
        }).reset_index()
        
        # Create charts
        st.line_chart(daily_transactions.set_index('transaction_date')['transaction_id'])
        
        st.write("**Daily Transaction Amount**")
        st.line_chart(daily_transactions.set_index('transaction_date')['transaction_amount'])
        
        # Merchant Category Analysis
        st.write("**Spending by Merchant Category**")
        
        # Group by merchant category
        mcc_spending = sales_df.groupby('merchant_category_code').agg({
            'transaction_amount': 'sum',
            'transaction_id': 'count',
            'customer_id': pd.Series.nunique
        }).reset_index()
        
        # Add category names
        mcc_spending['category_name'] = mcc_spending['merchant_category_code'].map(
            lambda x: MCC_CODES.get(x, 'Unknown')
        )
        
        # Sort and display
        category_chart_data = mcc_spending.sort_values('transaction_amount', ascending=False).head(10)
        st.bar_chart(category_chart_data.set_index('category_name')['transaction_amount'])
        
        # Weekend vs Weekday Analysis
        st.write("**Weekend vs Weekday Spending**")
        
        # Add day of week
        sales_df['day_of_week'] = sales_df['transaction_date'].dt.dayofweek
        sales_df['is_weekend'] = sales_df['day_of_week'] >= 5
        
        # Group by weekend flag
        weekend_data = sales_df.groupby('is_weekend').agg({
            'transaction_amount': ['sum', 'mean'],
            'transaction_id': 'count'
        })
        
        # Flatten multi-level columns
        weekend_data.columns = ['_'.join(col).strip() if isinstance(col, tuple) else col for col in weekend_data.columns]
        
        st.write("**Weekend vs Weekday Transaction Count**")
        st.bar_chart(weekend_data['transaction_id_count'])
        
        st.write("**Weekend vs Weekday Total Spend**")
        st.bar_chart(weekend_data['transaction_amount_sum'])
