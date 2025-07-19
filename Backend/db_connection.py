import pyodbc

def get_connection():
    return pyodbc.connect(
        'DRIVER={ODBC Driver 17 for SQL Server};'
        'SERVER=taskserver123.database.windows.net;'
        'DATABASE=TaskManager;'
        'UID=adminuser;'
        'PWD=StrongPassword@123;'
        'Encrypt=yes;'
        'TrustServerCertificate=no;'
        'Connection Timeout=30;'
    )
