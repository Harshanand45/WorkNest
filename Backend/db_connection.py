
import pyodbc

def get_connection():
    conn_str = (
        "DRIVER={ODBC Driver 18 for SQL Server};"
        "SERVER=taskserver123.database.windows.net;"
        "DATABASE=TaskManager;"
        "UID=adminuser;"
        "PWD=StrongPassword@123;"
        "Encrypt=yes;"
        "TrustServerCertificate=no;"
        "Connection Timeout=30;"
    )
    return pyodbc.connect(conn_str)
