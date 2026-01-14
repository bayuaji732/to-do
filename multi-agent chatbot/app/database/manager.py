"""
Database manager for S&P 500 dataset using DuckDB.
"""
import duckdb
import pandas as pd
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging

from app.database.metadata import DatabaseMetadataManager
from app.database.metadata import normalize_column_name

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages database operations with DuckDB."""
    
    def __init__(self, csv_path: str, db_path: str):
        self.csv_path = Path(csv_path)
        self.db_path = Path(db_path)
        self.metadata_manager = DatabaseMetadataManager()
        self.conn: Optional[duckdb.DuckDBPyConnection] = None
        
    def initialize(self):
        """Initialize database and load data."""
        logger.info("Initializing database...")
        
        # Create database directory if needed
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Connect to DuckDB
        self.conn = duckdb.connect(str(self.db_path))
        
        # Load CSV data
        if self.csv_path.exists():
            logger.info(f"Loading data from {self.csv_path}")

            df = pd.read_csv(self.csv_path)
            df.columns = [normalize_column_name(c) for c in df.columns]

            self.conn.execute("""
                CREATE OR REPLACE TABLE sp500_companies AS 
                SELECT * FROM df
            """)
            
            # Update row count in metadata
            row_count = self.conn.execute(
                "SELECT COUNT(*) FROM sp500_companies"
            ).fetchone()[0]
            self.metadata_manager.table_metadata.row_count = row_count
            
            logger.info(f"Loaded {row_count} rows")
        else:
            raise FileNotFoundError(f"Dataset not found at {self.csv_path}")
    
    def execute_query(self, query: str) -> pd.DataFrame:
        """
        Execute SQL query and return results as DataFrame.
        
        Args:
            query: SQL query string
            
        Returns:
            DataFrame with query results
        """
        if not self.conn:
            raise RuntimeError("Database not initialized")
        
        try:
            result = self.conn.execute(query).fetchdf()
            logger.info(f"Query executed successfully, returned {len(result)} rows")
            return result
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise
    
    def validate_query(self, query: str) -> tuple[bool, Optional[str]]:
        """
        Validate SQL query without executing it.
        
        Returns:
            (is_valid, error_message)
        """
        try:
            # Use EXPLAIN to validate without execution
            self.conn.execute(f"EXPLAIN {query}")
            return True, None
        except Exception as e:
            return False, str(e)
    
    def get_sample_data(self, limit: int = 5) -> pd.DataFrame:
        """Get sample rows from the dataset."""
        return self.execute_query(f"SELECT * FROM sp500_companies LIMIT {limit}")
    
    def get_column_stats(self, column: str) -> Dict[str, Any]:
        """Get statistics for a specific column."""
        col_info = self.metadata_manager.get_column_info(column)
        if not col_info:
            raise ValueError(f"Column '{column}' not found in schema")
        
        query = f"""
            SELECT 
                COUNT(*) as total_count,
                COUNT({column}) as non_null_count,
                COUNT(DISTINCT {column}) as distinct_count
            FROM sp500_companies
        """
        
        stats = self.execute_query(query).iloc[0].to_dict()
        
        # Add type-specific stats
        if col_info.data_type.value in ['integer', 'float']:
            numeric_query = f"""
                SELECT 
                    MIN({column}) as min_value,
                    MAX({column}) as max_value,
                    AVG({column}) as avg_value,
                    MEDIAN({column}) as median_value
                FROM sp500_companies
                WHERE {column} IS NOT NULL
            """
            numeric_stats = self.execute_query(numeric_query).iloc[0].to_dict()
            stats.update(numeric_stats)
        
        return stats
    
    def get_unique_values(self, column: str, limit: int = 20) -> List[str]:
        """Get unique values for a column."""
        if not self.metadata_manager.validate_column(column):
            raise ValueError(f"Column '{column}' not found in schema")
        
        query = f"""
            SELECT DISTINCT {column} 
            FROM sp500_companies 
            WHERE {column} IS NOT NULL
            ORDER BY {column}
            LIMIT {limit}
        """
        result = self.execute_query(query)
        return result[column].tolist()
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")