import pandas as pd
import glob
import os
from rapidfuzz import process, fuzz
import subprocess
import json
import re

# Root folder containing bank folders
folder = ".data"

# Full path to Ollama executable
ollama_path = r"C:\Users\Savanna\AppData\Local\Programs\Ollama\ollama.exe"

# Known banks and account types
known_banks = ["goldenwest", "chase", "wellsfargo", "amex"]
account_types = ["checking", "savings", "credit card", "imm"]

# Optimized categories
category_map = {
    "Housing": ["Mortgage/Rent", "Utilities", "Phone", "Cable/Internet", "Waste", "Maintenance/Repairs"],
    "Transportation": ["Vehicle Payments", "Insurance", "Fuel", "Licensing", "Parking", "Repairs", "Maintenance", "Other"],
    "Loans / Credit": ["Credit Card", "Student Loan", "House Loan", "Other"],
    "Insurance": ["Home/Rental", "Health", "Life", "Other"],
    "Taxes": ["Federal", "State", "Local", "Other"],
    "Savings / Investments": ["Emergency Fund", "Retirement", "Transfer to Savings", "Investments", "House Down Payment", "Other"],
    "Food / Dining": ["Groceries", "Restaurants/Dining", "Fast Food", "Snacks", "Other"],
    "Entertainment": ["Movies/Theater", "Music Platforms", "Concerts/Plays", "Games", "Hobbies", "Outdoor Recreation", "Travel", "Other"],
    "Personal Care / Health": ["Doctor/Dentist", "Medicine/Drugs", "Hair/Nails", "Health Club", "Discretionary", "Other"],
    "Education": ["Tuition", "Books", "Other"],
    "Gifts & Donations": ["Tithing", "Fast Offerings", "Gift", "Other"],
    "Vacations / Travel": ["Travel", "Lodging", "Food", "Entertainment", "Souvenirs", "Other"]
}

# # Function to categorize a single description using Ollama
# def categorize_transaction_cli(description):
#     if pd.isna(description) or description.strip() == "":
#         return {"main_category": "Other", "sub_category": "Other"}

#     prompt = f"""
#         You are a financial transaction categorizer.

#         Main categories:
#         Housing, Transportation, Loans / Credit, Insurance, Taxes,
#         Savings / Investments, Food / Dining, Entertainment,
#         Personal Care / Health, Education, Gifts & Donations, Vacations / Travel

#         Subcategories:
#         Use the relevant subcategory from the main category (for example, Mortgage/Rent under Housing).

#         Always respond ONLY in JSON format like:
#         {{"main_category": "...", "sub_category": "..."}}

#         Examples:
#         Transaction description: "Rent payment for August"
#         JSON: {{"main_category": "Housing", "sub_category": "Mortgage/Rent"}}

#         Transaction description: "Bought groceries at Walmart"
#         JSON: {{"main_category": "Food / Dining", "sub_category": "Groceries"}}

#         Transaction description: "Monthly credit card payment"
#         JSON: {{"main_category": "Loans / Credit", "sub_category": "Credit Card"}}

#         Now categorize this transaction description:
#         "{description}"
#     """

#     try:
#         result = subprocess.run(
#             [ollama_path, "chat", "mistral", "--prompt", prompt],
#             capture_output=True,
#             text=True,
#             timeout=15
#         )

#        # Print raw output for debugging
#         print(f"\n💡 Raw Ollama output for '{description}':\n{result.stdout}")

#         # Extract JSON using regex
#         match = re.search(r'\{.*\}', result.stdout, re.DOTALL)
#         if match:
#             return json.loads(match.group())
#         else:
#             return {"main_category": "Other", "sub_category": "Other"}

#     except Exception as e:
#         print(f"⚠️ Error categorizing '{description}': {e}")
#         return {"main_category": "Other", "sub_category": "Other"}

# # Helper to batch categorize multiple descriptions
# def categorize_descriptions_batch(descriptions):
#     results = []
#     for desc in descriptions:
#         results.append(categorize_transaction_cli(desc))
#     return results

# List to hold all banks
all_banks = []

# Scan folders in .data
bank_folders = [f.path for f in os.scandir(folder) if f.is_dir()]

for bank_folder in bank_folders:
    raw_bank_name = os.path.basename(bank_folder)

    # Fuzzy match bank name
    match_result = process.extractOne(raw_bank_name, known_banks, scorer=fuzz.ratio)
    bank_name = match_result[0]
    bank_score = match_result[1]
    print(f"Processing bank folder: {raw_bank_name} → matched to {bank_name} (score {bank_score})")

    # Find CSV files in the bank folder
    files = glob.glob(os.path.join(bank_folder, "*.csv"))
    bank_dfs = []

    for file in files:
        df = pd.read_csv(file)
        df.columns = df.columns.str.strip().str.lower()

        # Bank-specific column cleaning
        if bank_name == "goldenwest":
            df = df.rename(columns={
                "transaction date": "date",
                "description": "description",
                "amount": "amount",
            })
        elif bank_name == "capital one":
            df = df.rename(columns={
                "transaction date": "date",     # Transaction date     
                "description": "description",   # Merchant / transaction name
                "amount": "amount",             # Amount (positive = charge, negative = payment)
            })
            df["type"] = pd.melt(
                id_vars=[c for c in df.columns if c not in ["Debit", "Credit"]],
                value_vars=["Debit", "Credit"],
                var_name="type",
                value_name="mmount"
            ).dropna(subset=["amount"])
    

            

        elif bank_name == "sofi":
            # Typical SoFi CSV export columns
            df = df.rename(columns={
                "date" : "date",
                "merchant": "description",      # Merchant / transaction name
                "amount": "amount",             # Amount
                "running_balance": "balance"    # Running balance
            })

        # Convert date column
        df["date"] = pd.to_datetime(df["date"], errors="coerce")

        # Clean amount column
        df["amount"] = (
            df["amount"]
            .astype(str)
            .str.replace(",", "")
            .str.replace("(", "-")
            .str.replace(")", "")
            .astype(float)
        )

        # Add a "type" column based on the amount
        if account_name == "credit":
            df["amount"] = df["amount"] * -1  # Make all amounts reverse for credit card accounts
        df["type"] = df["amount"].apply(lambda x: "debit" if x > 0 else "credit")

        # Fuzzy match account type from filename
        filename_lower = os.path.basename(file).lower()
        match_result = process.extractOne(filename_lower, account_types, scorer=fuzz.ratio)
        account_name = match_result[0]

        df["bank"] = bank_name
        df["account"] = account_name

        # # Batch categorize descriptions
        # category_results = categorize_descriptions_batch(df["description"].tolist())
        # df["main_category"] = [r["main_category"] for r in category_results]
        # df["sub_category"] = [r["sub_category"] for r in category_results]

        bank_dfs.append(df)

    # Combine all accounts for this bank
    bank_combined = pd.concat(bank_dfs, ignore_index=True)
    all_banks.append(bank_combined)

# Combine all banks
combined = pd.concat(all_banks, ignore_index=True)
combined = combined.sort_values("date")

# Keep only necessary columns
columns_to_keep = ["date", "description", "type", "amount", "main_category", "sub_category", "bank", "account"]
combined = combined[columns_to_keep]

# Save final cleaned and categorized CSV
combined.to_csv("all_banks_final_categorized.csv", index=False)
print("✅ Done! Final cleaned and categorized CSV saved as 'all_banks_final_categorized.csv'.")









# # Read the bank statement CSV files
# def read_bank_statement(file_path):
#     try:
#         df = pd.read_csv(file_path)
#         return df
#     except Exception as e:
#         print(f"Error reading the file: {e}")
#         return None
    
# # Clean and preprocess the data
# def clean_data(df):
#     # Example cleaning steps
#     df.dropna(inplace=True)  # Remove missing values
#     df['Date'] = pd.to_datetime(df['Date'])  # Convert Date column to datetime
#     return df

# # Analyze the transactions
# def analyze_transactions(df):
#     # Example analysis: Calculate total income and expenses
#     total_income = df[df['Amount'] > 0]['Amount'].sum()
#     total_expenses = df[df['Amount'] < 0]['Amount'].sum()
#     return total_income, total_expenses

# # Generate a summary report
# def generate_summary_report(total_income, total_expenses):
#     report = f"Total Income: ${total_income:.2f}\nTotal Expenses: ${total_expenses:.2f}"
#     return report

# # Main function to process the bank statement
# def process_bank_statement(file_path):
#     df = read_bank_statement(file_path)
#     if df is not None:
#         df = clean_data(df)
#         total_income, total_expenses = analyze_transactions(df)
#         report = generate_summary_report(total_income, total_expenses)
#         print(report)