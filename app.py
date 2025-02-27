import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3
import os
from datetime import datetime, timedelta
import random
import string
import tempfile

# Set page config
st.set_page_config(layout="wide", page_title="Merchant Offers & Customer Dashboard")

# Add CSS for styling
st.markdown("""
<style>
    .main {
        padding: 1rem;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #f0f2f6;
        padding: 10px 20px;
        border-radius: 4px 4px 0 0;
    }
    .stTabs [aria-selected="true"] {
        background-color: #4e89ae;
        color: white;
    }
    .metric-card {
        background-color: #f9f9f9;
        border-radius: 10px;
        padding: 15px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# Ensure data directory exists
os.makedirs('data', exist_ok=True)

# Database paths
OFFERS_DB_PATH = 'data/offers_database.db'
CUSTOMERS_DB_PATH = 'data/customer_database.db'

# Function to ensure both databases exist
def ensure_databases_exist():
    # Check for offers database
    if not os.path.exists(OFFERS_DB_PATH):
        st.warning("Offers database not found. Please generate it first.")
        if st.button("Generate Offers Database"):
            with st.spinner("Generating offers database..."):
                # Execute the generator script (assuming it exists)
                try:
                    import subprocess
                    result = subprocess.run(["python", "generate_dummy_data.py"], capture_output=True, text=True)
                    if result.returncode == 0:
                        st.success("Offers database generated successfully!")
                    else:
                        st.error(f"Error generating offers database: {result.stderr}")
                except Exception as e:
                    st.error(f"Error executing generator script: {e}")
                    st.info("Please ensure generate_dummy_data.py is in the same directory.")
    
    # Check for customers database
    if not os.path.exists(CUSTOMERS_DB_PATH):
        st.warning("Customer database not found. Please generate it first.")
        if st.button("Generate Customer Database"):
            with st.spinner("Generating customer database..."):
                try:
                    import subprocess
                    result = subprocess.run(["python", "generate_customer_data.py"], capture_output=True, text=True)
                    if result.returncode == 0:
                        st.success("Customer database generated successfully!")
                    else:
                        st.error(f"Error generating customer database: {result.stderr}")
                except Exception as e:
                    st.error(f"Error executing generator script: {e}")
                    st.info("Please ensure generate_customer_data.py is in the same directory.")

# Function to load offers data with caching
@st.cache_data(ttl=300)
def load_offers_data(_conn, filters=None):
    query = "SELECT * FROM offers"
    params = []
    
    if filters:
        conditions = []
        
        if filters.get('merchant'):
            conditions.append("merchant = ?")
            params.append(filters['merchant'])
        
        if filters.get('category'):
            conditions.append("category = ?")
            params.append(filters['category'])
        
        if filters.get('type'):
            conditions.append("type = ?")
            params.append(filters['type'])
        
        if filters.get('min_discount') is not None:
            conditions.append("discount_percent >= ?")
            params.append(filters['min_discount'])
        
        if filters.get('max_discount') is not None:
            conditions.append("discount_percent <= ?")
            params.append(filters['max_discount'])
        
        if filters.get('active_only'):
            current_date = datetime.now().strftime('%Y-%m-%d')
            conditions.append("valid_until >= ?")
            params.append(current_date)
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
    
    return pd.read_sql_query(query, _conn)

# Function to get filter options for offers
@st.cache_data(ttl=300)
def get_offers_filter_options(_conn):
    merchants = pd.read_sql_query("SELECT DISTINCT merchant FROM offers ORDER BY merchant", _conn)['merchant'].tolist()
    categories = pd.read_sql_query("SELECT DISTINCT category FROM offers ORDER BY category", _conn)['category'].tolist()
    offer_types = pd.read_sql_query("SELECT DISTINCT type FROM offers ORDER BY type", _conn)['type'].tolist()
    
    return {
        'merchants': merchants,
        'categories': categories,
        'offer_types': offer_types
    }

# Function to load customers data with caching
@st.cache_data(ttl=300)
def load_customers_data(_conn, filters=None):
    query = "SELECT * FROM customers"
    params = []
    
    if filters:
        conditions = []
        
        if filters.get('customer_name'):
            conditions.append("customer_name LIKE ?")
            params.append(f"%{filters['customer_name']}%")
        
        if filters.get('mobile_type'):
            conditions.append("mobile_type = ?")
            params.append(filters['mobile_type'])
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
    
    return pd.read_sql_query(query, _conn)

# Function to get filter options for customers
@st.cache_data(ttl=300)
def get_customers_filter_options(_conn):
    mobile_types = pd.read_sql_query("SELECT DISTINCT mobile_type FROM customers ORDER BY mobile_type", _conn)['mobile_type'].tolist()
    return {
        'mobile_types': mobile_types
    }

# Function to add a real customer
def add_real_customer(conn, customer_name, mobile_number, email, mobile_type):
    cursor = conn.cursor()
    
    # Generate a new customer_id based on current max ID
    cursor.execute("SELECT MAX(SUBSTR(customer_id, 5)) FROM customers")
    max_id = cursor.fetchone()[0]
    if max_id is None:
        max_id = 0
    new_id = int(max_id) + 1
    customer_id = f"CUST{new_id:06d}"
    
    # Insert the new customer
    cursor.execute(
        "INSERT INTO customers (customer_id, customer_name, mobile_number, email, mobile_type) VALUES (?, ?, ?, ?, ?)",
        (customer_id, customer_name, mobile_number, email, mobile_type)
    )
    conn.commit()
    return customer_id

def main():
    # Check for and ensure databases exist
    ensure_databases_exist()
    
    # Title and description
    st.title("Merchant Offers & Customer Dashboard")
    st.markdown("Explore merchant offers and customer data for targeted marketing campaigns.")
    
    # Create tabs
    tabs = st.tabs(["Offers Dashboard", "Data Explorer", "Analytics", "Customers", "Targeting"])
    
    # Connect to databases
    try:
        offers_conn = sqlite3.connect(OFFERS_DB_PATH, check_same_thread=False)
        customers_conn = sqlite3.connect(CUSTOMERS_DB_PATH, check_same_thread=False)
    except Exception as e:
        st.error(f"Error connecting to database: {e}")
        return
    
    # ------------------- OFFERS DASHBOARD TAB -------------------
    with tabs[0]:
        st.header("Offers Overview")
        
        # Sidebar filters
        with st.sidebar:
            st.subheader("Filter Offers")
            
            try:
                filter_options = get_offers_filter_options(offers_conn)
            except Exception as e:
                st.error(f"Error loading filter options: {e}")
                filter_options = {"merchants": [], "categories": [], "offer_types": []}
            
            # Create filters
            selected_merchant = st.selectbox("Select Merchant", ["All"] + filter_options["merchants"])
            selected_category = st.selectbox("Select Category", ["All"] + filter_options["categories"])
            selected_type = st.selectbox("Select Offer Type", ["All"] + filter_options["offer_types"])
            
            min_discount, max_discount = st.slider("Discount Range (%)", 0, 100, (0, 100))
            active_only = st.checkbox("Active Offers Only", value=True)
            
            # Apply filters
            filters = {}
            if selected_merchant != "All":
                filters["merchant"] = selected_merchant
            if selected_category != "All":
                filters["category"] = selected_category
            if selected_type != "All":
                filters["type"] = selected_type
            
            filters["min_discount"] = min_discount
            filters["max_discount"] = max_discount
            filters["active_only"] = active_only
            
            if st.button("Reset Filters"):
                filters = {"active_only": True}
        
        # Load data
        try:
            df = load_offers_data(offers_conn, filters)
        except Exception as e:
            st.error(f"Error loading data: {e}")
            df = pd.DataFrame()
        
        if df.empty:
            st.info("No offers match your filters. Try adjusting your criteria.")
        else:
            # Display summary metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Offers", f"{len(df):,}")
            
            with col2:
                active_offers = df[df["valid_until"] >= datetime.now().strftime('%Y-%m-%d')]
                st.metric("Active Offers", f"{len(active_offers):,}")
            
            with col3:
                avg_discount = df["discount_percent"].mean()
                st.metric("Avg. Discount", f"{avg_discount:.1f}%")
            
            with col4:
                unique_merchants = df["merchant"].nunique()
                st.metric("Merchants", f"{unique_merchants:,}")
            
            # Charts
            st.subheader("Offer Distribution")
            col1, col2 = st.columns(2)
            
            with col1:
                by_type = df.groupby("type").size().reset_index(name="count")
                fig = px.pie(by_type, values="count", names="type", title="Offers by Type")
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                by_category = df.groupby("category").size().reset_index(name="count")
                by_category = by_category.sort_values("count", ascending=False).head(10)
                fig = px.bar(by_category, x="category", y="count", title="Top 10 Categories")
                st.plotly_chart(fig, use_container_width=True)
            
            # Discount range distribution
            fig = px.histogram(df, x="discount_percent", nbins=20, title="Discount Distribution")
            st.plotly_chart(fig, use_container_width=True)
            
            # Upcoming expiry
            st.subheader("Offers Expiring Soon")
            seven_days = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
            expiring_soon = df[(df["valid_until"] >= datetime.now().strftime('%Y-%m-%d')) & (df["valid_until"] <= seven_days)]
            
            if not expiring_soon.empty:
                st.dataframe(expiring_soon[["offer_id", "merchant", "description", "valid_until", "discount_percent"]])
            else:
                st.info("No offers expiring in the next 7 days.")
    
    # ------------------- DATA EXPLORER TAB -------------------
    with tabs[1]:
        st.header("Offers Data Explorer")
        
        # Load data (using the same filters from dashboard)
        try:
            df = load_offers_data(offers_conn, filters)
        except Exception as e:
            st.error(f"Error loading data: {e}")
            df = pd.DataFrame()
        
        if not df.empty:
            # Display the dataframe
            st.dataframe(df)
            
            # CSV download button
            csv = df.to_csv(index=False)
            st.download_button(
                label="Download Offers as CSV",
                data=csv,
                file_name="filtered_offers.csv",
                mime="text/csv"
            )
            
            # Display a random offer in detail
            st.subheader("Random Offer Details")
            if st.button("Show Random Offer"):
                random_offer = df.sample(1).iloc[0]
                
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**ID:** {random_offer['offer_id']}")
                    st.markdown(f"**Merchant:** {random_offer['merchant']}")
                    st.markdown(f"**Type:** {random_offer['type']}")
                    st.markdown(f"**Category:** {random_offer['category']}")
                
                with col2:
                    st.markdown(f"**Discount:** {random_offer['discount_percent']}%")
                    st.markdown(f"**Valid Until:** {random_offer['valid_until']}")
                    if 'coupon_code' in random_offer and random_offer['coupon_code']:
                        st.markdown(f"**Coupon Code:** {random_offer['coupon_code']}")
                
                st.markdown("---")
                st.markdown("**Description:**")
                st.markdown(f"{random_offer['description']}")
                
                if 'terms_conditions' in random_offer and random_offer['terms_conditions']:
                    st.markdown("**Terms & Conditions:**")
                    st.markdown(f"{random_offer['terms_conditions']}")
        else:
            st.info("No offers match your current filters.")
    
    # ------------------- ANALYTICS TAB -------------------
    with tabs[2]:
        st.header("Offers Analytics")
        
        try:
            # Load all data for analysis
            df = load_offers_data(offers_conn, {})
        except Exception as e:
            st.error(f"Error loading data: {e}")
            df = pd.DataFrame()
        
        if not df.empty:
            st.subheader("Merchant Analysis")
            
            # Merchant comparison
            merchant_stats = df.groupby("merchant").agg({
                "offer_id": "count",
                "discount_percent": "mean",
                "minimum_purchase": "mean"
            }).reset_index()
            
            merchant_stats.columns = ["Merchant", "Number of Offers", "Avg. Discount (%)", "Avg. Min Purchase"]
            merchant_stats = merchant_stats.sort_values("Number of Offers", ascending=False).head(20)
            
            fig = px.bar(merchant_stats, x="Merchant", y="Number of Offers", 
                        hover_data=["Avg. Discount (%)", "Avg. Min Purchase"],
                        title="Top 20 Merchants by Number of Offers")
            st.plotly_chart(fig, use_container_width=True)
            
            # Discount vs. minimum purchase scatter plot
            if 'minimum_purchase' in df.columns:
                st.subheader("Discount vs. Minimum Purchase Correlation")
                fig = px.scatter(df, x="minimum_purchase", y="discount_percent", 
                                color="merchant", size="discount_percent",
                                hover_name="merchant", log_x=True,
                                title="Discount % vs. Minimum Purchase")
                st.plotly_chart(fig, use_container_width=True)
            
            # Offer type analysis
            st.subheader("Offer Type Analysis")
            type_stats = df.groupby("type").agg({
                "offer_id": "count",
                "discount_percent": "mean"
            }).reset_index()
            
            col1, col2 = st.columns(2)
            
            with col1:
                fig = px.bar(type_stats, x="type", y="offer_id", 
                            title="Count by Offer Type")
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                fig = px.bar(type_stats, x="type", y="discount_percent", 
                            title="Avg. Discount by Type")
                st.plotly_chart(fig, use_container_width=True)
            
            # Time analysis if valid_from and valid_until exist
            if 'valid_from' in df.columns and 'valid_until' in df.columns:
                st.subheader("Offer Duration Analysis")
                
                # Convert date columns to datetime
                df['valid_from'] = pd.to_datetime(df['valid_from'])
                df['valid_until'] = pd.to_datetime(df['valid_until'])
                
                # Calculate duration in days
                df['duration'] = (df['valid_until'] - df['valid_from']).dt.days
                
                fig = px.histogram(df, x="duration", title="Offer Duration Distribution (Days)")
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No data available for analysis.")
    
    # ------------------- CUSTOMERS TAB -------------------
    with tabs[3]:
        st.header("Customer Database")
        
        # Sidebar filters for customers
        with st.sidebar:
            st.subheader("Filter Customers")
            
            try:
                customer_filter_options = get_customers_filter_options(customers_conn)
            except Exception as e:
                st.error(f"Error loading customer filter options: {e}")
                customer_filter_options = {"mobile_types": []}
            
            # Create filters
            customer_name_filter = st.text_input("Search by Name")
            selected_mobile_type = st.selectbox("Mobile Type", ["All"] + customer_filter_options["mobile_types"])
            
            # Apply filters
            customer_filters = {}
            if customer_name_filter:
                customer_filters["customer_name"] = customer_name_filter
            if selected_mobile_type != "All":
                customer_filters["mobile_type"] = selected_mobile_type
            
            if st.button("Reset Customer Filters"):
                customer_filters = {}
        
        # Load customer data
        try:
            customers_df = load_customers_data(customers_conn, customer_filters)
        except Exception as e:
            st.error(f"Error loading customer data: {e}")
            customers_df = pd.DataFrame()
        
        if customers_df.empty:
            st.info("No customers found matching your filters.")
        else:
            # Display summary metrics
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Customers", f"{len(customers_df):,}")
            
            with col2:
                ios_users = len(customers_df[customers_df["mobile_type"] == "iOS"])
                st.metric("iOS Users", f"{ios_users:,}")
            
            with col3:
                android_users = len(customers_df[customers_df["mobile_type"] == "Android"])
                st.metric("Android Users", f"{android_users:,}")
            
            # Distribution chart
            mobile_dist = customers_df.groupby("mobile_type").size().reset_index(name="count")
            fig = px.pie(mobile_dist, values="count", names="mobile_type", 
                        title="Mobile Type Distribution", color="mobile_type",
                        color_discrete_map={"iOS": "#A3AAEB", "Android": "#66DE93"})
            st.plotly_chart(fig, use_container_width=True)
            
            # Display customer table
            st.subheader("Customer Data")
            st.dataframe(customers_df)
            
            # CSV download button
            csv = customers_df.to_csv(index=False)
            st.download_button(
                label="Download Customers as CSV",
                data=csv,
                file_name="filtered_customers.csv",
                mime="text/csv"
            )
        
        # Add real customer section
        st.markdown("---")
        st.subheader("Add Real Customer")
        
        with st.form("add_customer_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                new_customer_name = st.text_input("Customer Name")
                new_mobile_number = st.text_input("Mobile Number")
            
            with col2:
                new_email = st.text_input("Email Address")
                new_mobile_type = st.selectbox("Mobile Type", ["iOS", "Android"])
            
            submit_button = st.form_submit_button("Add Customer")
        
        if submit_button:
            if not new_customer_name or not new_mobile_number or not new_email:
                st.error("Please fill in all required fields.")
            else:
                try:
                    customer_id = add_real_customer(
                        customers_conn, 
                        new_customer_name, 
                        new_mobile_number, 
                        new_email, 
                        new_mobile_type
                    )
                    st.success(f"Customer added successfully with ID: {customer_id}")
                    st.info("Refresh the page to see the updated customer list.")
                except Exception as e:
                    st.error(f"Error adding customer: {e}")
    
    # ------------------- TARGETING TAB -------------------
    with tabs[4]:
        st.header("Customer Offer Targeting")
        st.markdown("Match offers to customers based on various criteria")
        
        # Load data from both databases
        try:
            offers_df = load_offers_data(offers_conn, {"active_only": True})
            customers_df = load_customers_data(customers_conn, {})
        except Exception as e:
            st.error(f"Error loading data: {e}")
            offers_df = pd.DataFrame()
            customers_df = pd.DataFrame()
        
        if offers_df.empty or customers_df.empty:
            st.warning("Both offers and customers data must be available for targeting.")
        else:
            # Simple targeting options
            targeting_option = st.selectbox(
                "Select Targeting Method",
                ["Random Offers to Customers", "Mobile Type Targeted Offers", "Create Custom Campaign"]
            )
            
            if targeting_option == "Random Offers to Customers":
                # Generate random offer-customer pairings
                
                # Select number of offers per customer
                offers_per_customer = st.slider("Offers Per Customer", 1, 5, 3)
                
                if st.button("Generate Random Targeting"):
                    with st.spinner("Generating random offer-customer pairs..."):
                        # Create a dataframe to hold the results
                        results = []
                        
                        # For each customer, assign random offers
                        for _, customer in customers_df.sample(min(20, len(customers_df))).iterrows():
                            # Select random offers for this customer
                            for offer in offers_df.sample(min(offers_per_customer, len(offers_df))).iterrows():
                                results.append({
                                    "customer_id": customer["customer_id"],
                                    "customer_name": customer["customer_name"],
                                    "mobile_type": customer["mobile_type"],
                                    "offer_id": offer[1]["offer_id"],
                                    "merchant": offer[1]["merchant"],
                                    "offer_type": offer[1]["type"],
                                    "discount": f"{offer[1]['discount_percent']}%"
                                })
                        
                        # Display the results
                        results_df = pd.DataFrame(results)
                        st.subheader("Targeting Results")
                        st.dataframe(results_df)
                        
                        # Download option
                        csv = results_df.to_csv(index=False)
                        st.download_button(
                            label="Download Targeting Results",
                            data=csv,
                            file_name="targeting_results.csv",
                            mime="text/csv"
                        )
            
            elif targeting_option == "Mobile Type Targeted Offers":
                # Target offers based on mobile type
                st.markdown("Different offers for iOS vs Android users")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("iOS User Offers")
                    ios_categories = st.multiselect("Select Categories for iOS Users", 
                                                   sorted(offers_df["category"].unique()),
                                                   default=["Electronics", "Lifestyle"] if "Electronics" in offers_df["category"].unique() else None)
                
                with col2:
                    st.subheader("Android User Offers")
                    android_categories = st.multiselect("Select Categories for Android Users", 
                                                       sorted(offers_df["category"].unique()),
                                                       default=["Fashion", "Food"] if "Fashion" in offers_df["category"].unique() else None)
                
                if st.button("Generate Mobile-Targeted Campaign"):
                    with st.spinner("Creating mobile-targeted campaign..."):
                        # Create a dataframe to hold the results
                        results = []
                        
                        # For iOS users
                        ios_users = customers_df[customers_df["mobile_type"] == "iOS"].sample(min(10, len(customers_df[customers_df["mobile_type"] == "iOS"])))
                        ios_offers = offers_df[offers_df["category"].isin(ios_categories)]
                        
                        for _, customer in ios_users.iterrows():
                            # Select up to 3 offers for this iOS customer
                            for _, offer in ios_offers.sample(min(3, len(ios_offers))).iterrows():
                                results.append({
                                    "customer_id": customer["customer_id"],
                                    "customer_name": customer["customer_name"],
                                    "mobile_type": customer["mobile_type"],
                                    "offer_id": offer["offer_id"],
                                    "merchant": offer["merchant"],
                                    "category": offer["category"],
                                    "offer_type": offer["type"],
                                    "discount": f"{offer['discount_percent']}%"
                                })
                        
                        # For Android users
                        android_users = customers_df[customers_df["mobile_type"] == "Android"].sample(min(10, len(customers_df[customers_df["mobile_type"] == "Android"])))
                        android_offers = offers_df[offers_df["category"].isin(android_categories)]
                        
                        for _, customer in android_users.iterrows():
                            # Select up to 3 offers for this Android customer
                            for _, offer in android_offers.sample(min(3, len(android_offers))).iterrows():
                                results.append({
                                    "customer_id": customer["customer_id"],
                                    "customer_name": customer["customer_name"],
                                    "mobile_type": customer["mobile_type"],
                                    "offer_id": offer["offer_id"],
                                    "merchant": offer["merchant"],
                                    "category": offer["category"],
                                    "offer_type": offer["type"],
                                    "discount": f"{offer['discount_percent']}%"
                                })
                        
                        # Display the results
                        results_df = pd.DataFrame(results)
                        st.subheader("Mobile-Targeted Campaign Results")
                        st.dataframe(results_df)
                        
                        # Show summary stats
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("iOS Targets", len(results_df[results_df["mobile_type"] == "iOS"]))
                        with col2:
                            st.metric("Android Targets", len(results_df[results_df["mobile_type"] == "Android"]))
                        
                        # Download option
                        csv = results_df.to_csv(index=False)
                        st.download_button(
                            label="Download Campaign Results",
                            data=csv,
                            file_name="mobile_targeted_campaign.csv",
                            mime="text/csv"
                        )
            
            else:  # Custom Campaign
                st.subheader("Create Custom Targeting Campaign")
                st.info("In this section, you can create highly customized campaigns with specific targeting criteria.")
                
                # Campaign details
                campaign_name = st.text_input("Campaign Name", "Summer Special")
                
                # Select targeting criteria
                st.markdown("### Select Targeting Criteria")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**Customer Criteria**")
                    target_mobile_types = st.multiselect("Mobile Types", ["iOS", "Android"], default=["iOS", "Android"])
                    # Add more customer criteria as needed
                
                with col2:
                    st.markdown("**Offer Criteria**")
                    target_categories = st.multiselect("Categories", sorted(offers_df["category"].unique()))
                    min_discount = st.slider("Minimum Discount %", 0, 100, 20)
                    # Add more offer criteria as needed
                
                # Campaign settings
                st.markdown("### Campaign Settings")
                max_offers_per_customer = st.slider("Max Offers Per Customer", 1, 10, 5)
                
                if st.button("Generate Custom Campaign"):
                    with st.spinner("Creating custom campaign..."):
                        # Filter customers based on criteria
                        filtered_customers = customers_df[customers_df["mobile_type"].isin(target_mobile_types)]
                        
                        # Filter offers based on criteria
                        filtered_offers = offers_df[
                            (offers_df["category"].isin(target_categories) if target_categories else True) &
                            (offers_df["discount_percent"] >= min_discount)
                        ]
                        
                        if filtered_customers.empty or filtered_offers.empty:
                            st.error("No matches found with selected criteria.")
                        else:
                            # Create the campaign
                            results = []
                            
                            for _, customer in filtered_customers.sample(min(20, len(filtered_customers))).iterrows():
                                # Select offers for this customer
                                offers_for_customer = filtered_offers.sample(min(max_offers_per_customer, len(filtered_offers)))
                                
                                for _, offer in offers_for_customer.iterrows():
                                    results.append({
                                        "campaign": campaign_name,
                                        "customer_id": customer["customer_id"],
                                        "customer_name": customer["customer_name"],
                                        "mobile_type": customer["mobile_type"],
                                        "email": customer["email"],
                                        "offer_id": offer["offer_id"],
                                        "merchant": offer["merchant"],
                                        "category": offer["category"],
                                        "offer_type": offer["type"],
                                        "discount": f"{offer['discount_percent']}%",
                                        "valid_until": offer["valid_until"]
                                    })
                            
                            # Display the results
                            results_df = pd.DataFrame(results)
                            st.subheader(f"Campaign: {campaign_name}")
                            st.dataframe(results_df)
                            
                            # Download option
                            csv = results_df.to_csv(index=False)
                            st.download_button(
                                label=f"Download {campaign_name} Campaign",
                                data=csv,
                                file_name=f"{campaign_name.lower().replace(' ', '_')}_campaign.csv",
                                mime="text/csv"
                            )
    
    # Close database connections
    offers_conn.close()
    customers_conn.close()

if __name__ == "__main__":
    main()
