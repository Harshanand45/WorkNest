

import pymssql

def get_connection():
    return pymssql.connect(
        server='taskserver123.database.windows.net',
        user='adminuser',
        password='StrongPassword@123',
        database='TaskManager'
    )
