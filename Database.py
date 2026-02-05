import mysql.connector
from mysql.connector import Error
import json
import os


class Database:
    """
    Simple wrapper class for MySQL connection used by the Streamlit app.
    """

    def __init__(self):
        """
        Create a connection to the MySQL database.
        """
        try:
            self.conn = mysql.connector.connect(
                host="localhost",
                user="root",
                password=os.getenv("DB_PASSWORD"),
                database="DB_FinSight",
            )

            if self.conn.is_connected():
                self.cursor = self.conn.cursor()
                print("Connected to the database successfully")
            else:
                raise Error("Failed to connect to the database")

        except Error as err:
            # In a Streamlit app this will also show up in the logs
            print(f"Error in connection: {err}")
            self.conn = None
            self.cursor = None

    def insert_invoice(self, store_name, date, total_amount, category, items):
        """
        Insert invoice into `invoices` table AND items into `invoice_items` table.
        """
        # Check if the connection is established
        if not self.conn or not self.cursor:
            # Try to reconnect if the connection is lost
            self.connect()
            if not self.conn or not self.cursor:
                raise RuntimeError("Database connection is not available")

        try:

         # Insert invoice into `invoices` table
            sql_invoice = """
                INSERT INTO invoices (store_name, invoice_date, total_amount, category)
                VALUES (%s, %s, %s, %s)
            """
            values_invoice = (store_name, date, total_amount, category)

            self.cursor.execute(sql_invoice, values_invoice)

            # Get the new invoice ID
            new_invoice_id = self.cursor.lastrowid

            # Insert items into `invoice_items` table
            sql_items = """
                INSERT INTO invoice_items (invoice_id, item_name, quantity, price)
                VALUES (%s, %s, %s, %s)
            """

            for item in items:
                name = item.get('name', 'Unknown')
                qty = item.get('quantity', 1)
                price = item.get('price', 0.0)

                # Save the item and link it to the invoice (new_invoice_id)
                self.cursor.execute(
                    sql_items, (new_invoice_id, name, qty, price))

            self.conn.commit()
            return True

        except Error as err:
            print(f"Error inserting invoice: {err}")
            if self.conn:
                self.conn.rollback()
            return False

    def close(self):
        """
        Cleanly close cursor and connection.
        """
        if self.cursor:
            self.cursor.close()
        if self.conn and self.conn.is_connected():
            self.conn.close()
            print("Connection closed")

    def __del__(self):
        # Ensure resources are freed when the object is garbage-collected
        try:
            self.close()
        except Exception:
            pass

    def fetch_all_invoices(self):

        if not self.conn or not self.cursor:
            self.connect()

        try:
            # Using LEFT JOIN to link the invoice with its items
            # Using GROUP_CONCAT to combine items into a single string
            query = """
            SELECT 
                i.id, 
                i.store_name, 
                i.invoice_date, 
                i.total_amount, 
                i.category,
                COALESCE(GROUP_CONCAT(it.item_name SEPARATOR ', '), 'No Items') as items
            FROM invoices i
            LEFT JOIN invoice_items it ON i.id = it.invoice_id
            GROUP BY i.id
            ORDER BY i.invoice_date DESC
            """

            self.cursor.execute(query)
            return self.cursor.fetchall()

        except Exception as e:
            print(f"Error fetching data: {e}")
            return []

    def close(self):
        if self.cursor:
            self.cursor.close()
        if self.conn and self.conn.is_connected():
            self.conn.close()
