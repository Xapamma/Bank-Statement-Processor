# Bank-Statement-Processor

This repository contains a Python project that automates the process of compiling, cleaning, and categorizing bank transaction data from multiple banks. The goal is to streamline financial analysis and help track spending across different categories efficiently.

---

## Table of Contents
- [Introduction](#introduction)
- [Motivation](#motivation)
- [Ethical Considerations](#ethical-considerations)
- [Project Structure](#project-structure)
- [Requirements](#requirements)
- [Usage](#usage)
- [How It Works](#how-it-works)

---

## Introduction
For years, manually compiling bank statements into a single Excel sheet was time-consuming and prone to errors. This project automates the process using Python, reading CSV files from multiple banks, cleaning and standardizing the data, categorizing transactions, and compiling them into a single dataset ready for analysis.

---

## Motivation
The project was inspired by the need to answer questions like:
- "Am I spending too much in certain categories?"
- "How can I optimize my budget?"

By automating transaction categorization and compilation, it is possible to analyze spending habits more accurately and regularly.

---

## Ethical Considerations
Financial data is sensitive. This project prioritizes privacy and security:
- All data processing occurs locally.
- No personal financial information is shared with third parties.
- CSV files are manually downloaded from bank accounts rather than scraping websites, avoiding potential security or legal issues.

---

## Project Structure
- .data/ # Folder containing bank CSV files

    - goldenwest/ # Bank-specific folders

    - chase/

    - ...

- all_banks_final_categorized.csv # Output file with cleaned and categorized transactions

- bank_statement.py # Python script for cleaning and categorizing

- README.md

---

## Requirements
- Python 3.10+
- Libraries:
  - `pandas`
  - `rapidfuzz`
  - `subprocess` (standard library)
  - `json` (standard library)
  - `re` (standard library)
- [Ollama](https://ollama.com) installed locally for AI-assisted categorization

---

## Usage
1. Place CSV files from your banks into the `.data` folder, separated by bank.
2. Adjust the `known_banks` and `account_types` lists in `bank_statement_processor.py` if needed.
3. Update the `ollama_path` variable to your local Ollama executable.
4. Run the script:
```bash
python bank_statement_processor.py
```

The script outputs all_banks_final_categorized.csv with the following columns:

- date
- description
- type
- amount
- main_category
- sub_category
- bank
- account


## How It Works

Data Collection: CSV files are manually downloaded from each bank for the relevant time period.

Data Cleaning: The script standardizes column names, formats dates, and converts amounts to floats.

String Matching & Categorization: Transaction descriptions are categorized using fuzzy string matching (RapidFuzz) and AI-assisted categorization via Ollama.

Data Compilation: Transactions from all banks are combined into a single dataset and sorted by date for analysis.