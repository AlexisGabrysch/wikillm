# FILE: src/metrics_database.py
import sqlite3
from typing import List, Dict, Any
from datetime import datetime

class RAGMetricsDatabase:
    def __init__(self, db_path: str = "src/db/rag_metrics.db") -> None:
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.create_table()

    def create_table(self) -> None:
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS rag_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME,
                input_tokens INTEGER,
                output_tokens INTEGER,
                price_input REAL,
                price_output REAL,
                latency REAL,
                gwp REAL,
                energy_usage REAL
            )
        """)
        self.conn.commit()

    def insert_metric(
        self,
        input_tokens: int,
        output_tokens: int,
        price_input: float,
        price_output: float,
        latency: float,
        gwp: float,
        energy_usage: float,
        timestamp: str = None
        
    ) -> int:
        """
        Inserts a new metric record into the rag_metrics table.
        If timestamp is not provided, current datetime in ISO format is used.
        """
        if timestamp is None:
            timestamp = datetime.now().isoformat()
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO rag_metrics (timestamp, input_tokens, output_tokens, price_input, price_output, latency , gwp, energy_usage)
            VALUES (?, ?, ?, ?, ?, ? , ?, ?)
        """, (timestamp, input_tokens, output_tokens, price_input, price_output, latency, gwp, energy_usage))
        self.conn.commit()
        return cursor.lastrowid

    def get_all_metrics(self) -> List[Dict[str, Any]]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM rag_metrics")
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in rows]

    def get_average_metrics(self) -> Dict[str, float]:
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT 
                AVG(latency) AS avg_latency,
                AVG(price_input) AS avg_price_input,
                AVG(price_output) AS avg_price_output
            FROM rag_metrics
        """)
        row = cursor.fetchone()
        return {
            "avg_latency": row[0],
            "avg_price_input": row[1],
            "avg_price_output": row[2]
        }

    def close(self) -> None:
        self.conn.close()

# Example usage (can be removed in production)
if __name__ == "__main__":
    print("Creating RAGMetricsDatabase object...")