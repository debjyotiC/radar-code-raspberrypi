import sqlite3
import numpy as np
import threading


class DatabaseConnector:
    def __init__(self, db_file):
        self.conn = None
        self.db_file = db_file
        self.lock = threading.Lock()  # Create a lock for synchronization

    def connect(self):
        self.conn = sqlite3.connect(self.db_file, isolation_level=None, timeout=10, check_same_thread=False)

    def close(self):
        if self.conn:
            self.conn.close()
            self.conn = None

    def fetch_data(self, key1, key2, key3, key4):
        with self.lock:  # Acquire the lock before accessing the database
            conn = sqlite3.connect(self.db_file)
            query = "SELECT * FROM radar_data WHERE key_1=? AND key_2=? AND key_3=? AND key_4=?"
            cursor = conn.cursor()
            cursor.execute(query, (key1, key2, key3, key4))
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
            return rows

    def fetch_updated_data(self, key1, key2, key3, key4):
        with self.lock:
            conn = sqlite3.connect(self.db_file)
            query = "SELECT * FROM radar_data WHERE key_1=? AND key_2=? AND key_3=? AND key_4=?"
            cursor = conn.cursor()
            cursor.execute(query, (key1, key2, key3, key4))
            conn.commit()
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
            return rows

    def fetch_matrix_values(self, reshape_1, reshape_2):
        with self.lock:
            conn = sqlite3.connect(self.db_file)
            query = "SELECT matrix_values FROM rdv_mat ORDER BY id DESC LIMIT 1"
            cursor = conn.cursor()
            cursor.execute(query)
            row = cursor.fetchone()
            cursor.close()
            conn.close()
            if row:
                values_blob = row[0]
                rdv_matrix = np.frombuffer(values_blob, dtype=np.float32).reshape((reshape_1, reshape_2))
                return rdv_matrix
            else:
                return None

    def fetch_updated_matrix_values(self, reshape_1, reshape_2):
        with self.lock:
            conn = sqlite3.connect(self.db_file)
            query = "SELECT matrix_values FROM rdv_mat WHERE id=last_insert_rowid()"
            cursor = conn.cursor()
            cursor.execute(query)
            row = cursor.fetchone()
            cursor.close()
            conn.close()
            if row:
                values_blob = row[0]
                rdv_matrix = np.frombuffer(values_blob, dtype=np.float32).reshape((reshape_1, reshape_2))
                return rdv_matrix
            else:
                return None

    def insert_data(self, key1, value1, key2, value2, key3, value3, key4, value4):
        with self.lock:
            conn = sqlite3.connect(self.db_file)
            query = "INSERT INTO radar_data VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
            cursor = conn.cursor()
            cursor.execute(query, (key1, value1, key2, value2, key3, value3, key4, value4))
            conn.commit()
            cursor.close()
            conn.close()

    def insert_rdv_matrix(self, rdv_matrix, timestamp):
        with self.lock:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            rdv_blob = rdv_matrix.tobytes()
            query = "INSERT INTO rdv_mat (matrix_values, timestamp) VALUES (?, ?)"
            cursor.execute(query, (rdv_blob, timestamp))
            conn.commit()
            cursor.close()
            conn.close()
