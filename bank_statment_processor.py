import pandas as pd
import numpy as np
import glob
import os
from rapidfuzz import process, fuzz
import subprocess
import json
import re
from cleaning_logic import clean_and_categorize

# Root folder containing bank folders
folder = ".data"

# Full path to Ollama executable
ollama_path = r"C:\Users\Savanna\AppData\Local\Programs\Ollama\ollama.exe"

# Known banks and account types
known_banks = ["goldenwest", "sofi", "capital one"]
account_map = {
    "cc": "credit card",
    "credit card": "credit card",
    "checking": "checking",
    "savings": "savings",
    "imm": "money market",
    "gold": "gold account"
}

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
                "posting date": "date",
                "description": "description",
                "amount": "amount",
                "type" : "category type"
            })

        elif bank_name == "capital one":
            df = df.rename(columns={
                "transaction date": "date",        
                "description": "description",           
            })
            # Make into one column
            df = pd.melt(
                df,
                id_vars=[c for c in df.columns if c not in ["debit", "credit"]],
                value_vars=["debit", "credit"],
                var_name="type",
                value_name="amount"
            ).dropna(subset=["amount"])

        elif bank_name == "sofi":
            # Typical SoFi CSV export columns
            df = df.rename(columns={
                "date" : "date",
                "description": "description",     
                "amount": "amount"            
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

        # Fuzzy match account type from filename
        filename_lower = os.path.basename(file).lower()
        match_result = process.extractOne(filename_lower, account_map.keys(), scorer=fuzz.partial_ratio)
        
        # Get a clean name from the map
        matched_key = match_result[0]
        account_name = account_map[matched_key]

        df["bank"] = bank_name
        df["account"] = account_name

        # Add a "type" column based on the amount
        # If credit card, make debits negative
        if account_name == "credit card":
            df.loc[df["type"] == "debit", "amount"] = -df["amount"].abs()  # Make all debit amounts negative for charges
            df.loc[df["type"] == "credit", "amount"] = df["amount"].abs()  # Make all credit amounts positive for payments or reimbursements
        else:
            df["type"] = np.where(df["amount"] > 0, "credit", "debit")

        bank_dfs.append(df)

    # Combine all accounts for this bank
    bank_combined = pd.concat(bank_dfs, ignore_index=True)
    all_banks.append(bank_combined)

# Combine all banks
combined = pd.concat(all_banks, ignore_index=True)
combined = combined.sort_values("date")

# Placeholder for now
combined["sub_category"] = np.nan
combined["main_category"] = np.nan

# Keep only necessary columns
columns_to_keep = ["date", "description", "type", "amount", "main_category", "sub_category", "bank", "account"]
combined = combined[columns_to_keep]

# Final Step: Apply the robust cleaning logic
print("Applying categorization logic...")
final_df = clean_and_categorize(combined)

# Save
final_df.to_csv("all_banks_final_categorized.csv", index=False)

print("✅ Done! Final cleaned and categorized CSV saved as 'all_banks_final_categorized.csv'.")
