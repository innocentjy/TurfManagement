# database.py
import pyodbc

def get_connection():
    return pyodbc.connect(
        'DRIVER={ODBC Driver 17 for SQL Server};'
        'SERVER=localhost\MSSQL2019;'
        'DATABASE=TurfManagement;'
        'Trusted_Connection=yes;'
    )

def get_cursor():
    return get_connection().cursor()
