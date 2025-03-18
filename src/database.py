import sys
import os
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import config

load_dotenv()

# PostgreSQL connection details
DB_NAME = os.getenv("POSTGRES_DB", "ynab_data")
DB_USER = os.getenv("POSTGRES_USER", "ynab_user")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "ynab_password")
DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")

def get_db_connection():
    """Create and return a PostgreSQL database connection."""
    return psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )

def create_schemas():
    """Create database schemas if they don't exist."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("CREATE SCHEMA IF NOT EXISTS EtlStage;")
    cursor.execute("CREATE SCHEMA IF NOT EXISTS YnabData;")
    cursor.execute("CREATE SCHEMA IF NOT EXISTS YnabData_History;")

    conn.commit()
    conn.close()
    print("Schemas created successfully.")

def create_tables():
    """Create tables within their respective schemas."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # EtlStage.TransactionsJson
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS EtlStage.TransactionsJson (
            Id TEXT PRIMARY KEY,
            TransactionData JSONB NOT NULL,
            CreatedDateTime TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ProcessedDateTime TIMESTAMP NULL
        );
    """)

    # YnabData_History.Transactions
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS YnabData_History.Transactions (
            RecordStartDateTime TIMESTAMP NOT NULL,
            RecordEndDateTime TIMESTAMP NULL,
            Id TEXT PRIMARY KEY,
            Date TEXT NOT NULL,
            Amount INTEGER NOT NULL,
            Memo TEXT,
            Cleared TEXT NOT NULL,
            Approved BOOLEAN NOT NULL,
            Flag_Color TEXT,
            Flag_Name TEXT,
            Account_Id TEXT NOT NULL,
            Account_Name TEXT NOT NULL,
            Payee_Id TEXT,
            Payee_Name TEXT,
            Category_Id TEXT,
            Category_Name TEXT,
            Transfer_Account_Id TEXT,
            Transfer_Transaction_Id TEXT,
            Matched_Transaction_Id TEXT,
            Import_Id TEXT,
            Import_Payee_Name TEXT,
            Import_Payee_Name_Original TEXT,
            Debt_Transaction_Type TEXT,
            Deleted BOOLEAN NOT NULL,
            RowHash TEXT NOT NULL
        );
    """)

    # 3. Create YnabData_History.Subtransactions
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS YnabData_History.Subtransactions (
            RecordStartDateTime TIMESTAMP NOT NULL,
            RecordEndDateTime TIMESTAMP NULL,
            Id TEXT PRIMARY KEY,
            Transaction_Id TEXT NOT NULL,
            FOREIGN KEY (Transaction_Id) REFERENCES YnabData_History.Transactions(Id)
        );
    """)

    conn.commit()
    conn.close()
    print("Tables created successfully.")

if __name__ == "__main__":
    create_schemas()
    create_tables()
