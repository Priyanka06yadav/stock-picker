import streamlit as st
import requests
import pandas as pd
import datetime

# Configuration
BACKEND_URL = "http://localhost:8000" # Assuming the FastAPI backend runs on this URL

# --- Helper Functions for Backend API Calls ---
def create_account(initial_deposit: float):
    try:
        response = requests.post(f"{BACKEND_URL}/accounts/", json={"initial_deposit": initial_deposit})
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error creating account: {e}")
        return None

def get_account_details(account_id: int):
    try:
        response = requests.get(f"{BACKEND_URL}/accounts/{account_id}/")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching account details: {e}")
        return None

def deposit_funds(account_id: int, amount: float):
    try:
        response = requests.post(f"{BACKEND_URL}/accounts/{account_id}/deposit/", json={"amount": amount})
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error depositing funds: {e}")
        return None

def withdraw_funds(account_id: int, amount: float):
    try:
        response = requests.post(f"{BACKEND_URL}/accounts/{account_id}/withdraw/", json={"amount": amount})
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error withdrawing funds: {e}")
        return None

def buy_stock(account_id: int, symbol: str, quantity: float):
    try:
        response = requests.post(f"{BACKEND_URL}/accounts/{account_id}/buy/", json={"symbol": symbol, "quantity": quantity})
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error buying stock: {e}")
        return None

def sell_stock(account_id: int, symbol: str, quantity: float):
    try:
        response = requests.post(f"{BACKEND_URL}/accounts/{account_id}/sell/", json={"symbol": symbol, "quantity": quantity})
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error selling stock: {e}")
        return None

def get_holdings(account_id: int):
    try:
        response = requests.get(f"{BACKEND_URL}/accounts/{account_id}/holdings/")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching holdings: {e}")
        return []

def get_transactions(account_id: int):
    try:
        response = requests.get(f"{BACKEND_URL}/accounts/{account_id}/transactions/")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching transactions: {e}")
        return []

def get_portfolio_summary(account_id: int):
    try:
        response = requests.get(f"{BACKEND_URL}/accounts/{account_id}/portfolio-summary/")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching portfolio summary: {e}")
        return None

# --- Streamlit Application Layout ---
st.set_page_config(layout="wide", page_title="Stock Portfolio Manager")

st.title("📈 Stock Portfolio Manager")

# Initialize session state for account_id
if 'account_id' not in st.session_state:
    st.session_state.account_id = None

# Sidebar for account management
with st.sidebar:
    st.header("Account Management")

    # Create Account Section
    st.subheader("Create New Account")
    with st.form("create_account_form"):
        initial_deposit = st.number_input("Initial Deposit", min_value=0.01, value=1000.00, step=100.00)
        create_account_button = st.form_submit_button("Create Account")
        if create_account_button:
            new_account = create_account(initial_deposit)
            if new_account:
                st.session_state.account_id = new_account['id']
                st.success(f"Account created successfully! Account ID: {st.session_state.account_id}")
                st.rerun()

    st.markdown("---")

    # Select Existing Account Section
    st.subheader("Select Existing Account")
    current_account_id_input = st.number_input("Enter Account ID", min_value=1, value=st.session_state.account_id if st.session_state.account_id else 1, step=1)
    select_account_button = st.button("Select Account")
    if select_account_button:
        account_details = get_account_details(current_account_id_input)
        if account_details:
            st.session_state.account_id = current_account_id_input
            st.success(f"Account {st.session_state.account_id} selected.")
            st.rerun()
        else:
            st.error("Account not found.")

    st.markdown("---")

    if st.session_state.account_id:
        st.info(f"Currently managing Account ID: **{st.session_state.account_id}**")
        if st.button("Deselect Account"):
            st.session_state.account_id = None
            st.rerun()

# Main Content Area
if st.session_state.account_id:
    st.header(f"Dashboard for Account ID: {st.session_state.account_id}")

    # --- Portfolio Summary ---
    st.subheader("Portfolio Summary")
    summary = get_portfolio_summary(st.session_state.account_id)
    if summary:
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("Cash Balance", f"\${summary['cash_balance']:.2f}")
        with col2:
            st.metric("Stock Holdings Value", f"\${summary['stock_holdings_value']:.2f}")
        with col3:
            st.metric("Total Portfolio Value", f"\${summary['total_portfolio_value']:.2f}")
        with col4:
            st.metric("Initial Deposit", f"\${summary['initial_deposit']:.2f}")
        with col5:
            # Determine color for profit/loss
            if summary['profit_loss'] >= 0:
                st.metric("Profit/Loss", f"\${summary['profit_loss']:.2f}", delta_color="green")
            else:
                st.metric("Profit/Loss", f"\${summary['profit_loss']:.2f}", delta_color="red")
    else:
        st.warning("Could not load portfolio summary.")
    
    st.markdown("---")

    # --- Tabs for Actions and Data ---
    tab1, tab2, tab3, tab4 = st.tabs(["Funds & Trades", "Current Holdings", "Transaction History", "Account Details"])

    with tab1:
        st.subheader("Deposit / Withdraw Funds")
        col_deposit, col_withdraw = st.columns(2)
        with col_deposit:
            with st.form("deposit_form"):
                deposit_amount = st.number_input("Deposit Amount", min_value=0.01, value=100.00, step=10.00)
                deposit_button = st.form_submit_button("Deposit")
                if deposit_button:
                    account_response = deposit_funds(st.session_state.account_id, deposit_amount)
                    if account_response:
                        st.success(f"Deposited \${deposit_amount:.2f}.")
                        st.rerun()
        with col_withdraw:
            with st.form("withdraw_form"):
                withdraw_amount = st.number_input("Withdraw Amount", min_value=0.01, value=50.00, step=10.00)
                withdraw_button = st.form_submit_button("Withdraw")
                if withdraw_button:
                    account_response = withdraw_funds(st.session_state.account_id, withdraw_amount)
                    if account_response:
                        st.success(f"Withdrew \${withdraw_amount:.2f}.")
                        st.rerun()

        st.markdown("---")

        st.subheader("Buy / Sell Stocks")
        col_buy, col_sell = st.columns(2)
        with col_buy:
            with st.form("buy_stock_form"):
                buy_symbol = st.text_input("Stock Symbol to Buy (e.g., AAPL)", "AAPL").upper()
                buy_quantity = st.number_input("Quantity to Buy", min_value=0.01, value=1.0, step=0.1)
                buy_button = st.form_submit_button("Buy Stock")
                if buy_button:
                    transaction_response = buy_stock(st.session_state.account_id, buy_symbol, buy_quantity)
                    if transaction_response:
                        st.success(f"Bought {buy_quantity} shares of {buy_symbol}.")
                        st.rerun()
        with col_sell:
            with st.form("sell_stock_form"):
                sell_symbol = st.text_input("Stock Symbol to Sell (e.g., AAPL)", "AAPL").upper()
                sell_quantity = st.number_input("Quantity to Sell", min_value=0.01, value=1.0, step=0.1)
                sell_button = st.form_submit_button("Sell Stock")
                if sell_button:
                    transaction_response = sell_stock(st.session_state.account_id, sell_symbol, sell_quantity)
                    if transaction_response:
                        st.success(f"Sold {sell_quantity} shares of {sell_symbol}.")
                        st.rerun()

    with tab2:
        st.subheader("Current Stock Holdings")
        holdings_data = get_holdings(st.session_state.account_id)
        if holdings_data:
            df_holdings = pd.DataFrame(holdings_data)
            st.dataframe(df_holdings)
        else:
            st.info("No stock holdings found for this account.")

    with tab3:
        st.subheader("Transaction History")
        transactions_data = get_transactions(st.session_state.account_id)
        if transactions_data:
            df_transactions = pd.DataFrame(transactions_data)
            # Format timestamp for better readability
            df_transactions['timestamp'] = pd.to_datetime(df_transactions['timestamp']).dt.strftime('%Y-%m-%d %H:%M:%S')
            st.dataframe(df_transactions)
        else:
            st.info("No transactions found for this account.")
    
    with tab4:
        st.subheader("Account Details")
        account_details = get_account_details(st.session_state.account_id)
        if account_details:
            st.write(f"**Account ID:** {account_details['id']}")
            st.write(f"**Initial Deposit:** \${account_details['initial_deposit']:.2f}")
            st.write(f"**Current Cash Balance:** \${account_details['cash_balance']:.2f}")
        else:
            st.warning("Could not retrieve full account details.")


else:
    st.info("Please create a new account or select an existing account from the sidebar to get started.")
