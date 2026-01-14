"""
Database metadata management for schema-aware querying.
"""
from dataclasses import dataclass
import re
from typing import List, Dict, Optional
from enum import Enum
import pandas as pd
from pathlib import Path

class DataType(Enum):
    """Supported data types in the dataset."""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    DATE = "date"
    BOOLEAN = "boolean"


@dataclass
class ColumnMetadata:
    """Metadata for a single column."""
    name: str
    data_type: DataType
    unit: Optional[str]
    description: str
    example_values: List[str]
    nullable: bool = True
    
    def to_llm_description(self) -> str:
        """Generate LLM-friendly description."""
        desc = f"- {self.name} ({self.data_type.value}): {self.description}"
        if self.unit:
            desc += f" [Unit: {self.unit}]"
        if self.example_values:
            desc += f" [Examples: {', '.join(map(str, self.example_values[:3]))}]"
        return desc


@dataclass
class TableMetadata:
    """Metadata for the entire table."""
    name: str
    description: str
    columns: List[ColumnMetadata]
    row_count: int
    time_granularity: Optional[str] = None
    
    def get_column(self, name: str) -> Optional[ColumnMetadata]:
        """Get column metadata by name."""
        normalized = normalize_column_name(name)
        for col in self.columns:
            if col.name == normalized:
                return col
        return None
    
    def to_llm_schema(self) -> str:
        """Generate complete schema description for LLM."""
        schema = f"Table: {self.name}\n"
        schema += f"Description: {self.description}\n"
        schema += f"Total Rows: {self.row_count}\n"
        if self.time_granularity:
            schema += f"Time Granularity: {self.time_granularity}\n"
        schema += "\nColumns:\n"
        for col in self.columns:
            schema += col.to_llm_description() + "\n"
        return schema


def build_sp500_metadata() -> TableMetadata:
    """Build metadata for S&P 500 dataset by auto-detecting from CSV."""
    csv_path = Path("data/sp500_companies.csv")
    
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found at {csv_path}")
    
    # Auto-detect from CSV
    df = pd.read_csv(csv_path)
    columns = []
    
    # Define column descriptions and units
    column_info = {
        "Symbol": {
            "description": "Stock ticker symbol",
            "unit": None
        },
        "Name": {
            "description": "Company name",
            "unit": None
        },
        "Sector": {
            "description": "GICS sector classification",
            "unit": None
        },
        "Price": {
            "description": "Current stock price",
            "unit": "USD"
        },
        "Price/Earnings": {
            "description": "Price-to-Earnings ratio",
            "unit": "ratio"
        },
        "Dividend Yield": {
            "description": "Annual dividend yield",
            "unit": "percentage"
        },
        "Earnings/Share": {
            "description": "Earnings per share",
            "unit": "USD"
        },
        "52 Week Low": {
            "description": "52-week low stock price",
            "unit": "USD"
        },
        "52 Week High": {
            "description": "52-week high stock price",
            "unit": "USD"
        },
        "Market Cap": {
            "description": "Market capitalization",
            "unit": "USD"
        },
        "EBITDA": {
            "description": "Earnings before interest, taxes, depreciation, and amortization",
            "unit": "USD"
        },
        "Price/Sales": {
            "description": "Price-to-Sales ratio",
            "unit": "ratio"
        },
        "Price/Book": {
            "description": "Price-to-Book ratio",
            "unit": "ratio"
        },
        "SEC Filings": {
            "description": "SEC filings URL",
            "unit": None
        }
    }
    
    for col_name in df.columns:
        # Determine data type
        dtype = df[col_name].dtype
        
        if dtype == 'object':
            data_type = DataType.STRING
        elif dtype in ['int64', 'int32', 'int16', 'int8']:
            data_type = DataType.INTEGER
        elif dtype in ['float64', 'float32']:
            data_type = DataType.FLOAT
        else:
            data_type = DataType.STRING
        
        # Get sample values (non-null, first 3)
        sample_values = df[col_name].dropna().head(3).astype(str).tolist()
        
        # Get description and unit from predefined info
        info = column_info.get(col_name, {})
        description = info.get("description", col_name.replace('_', ' '))
        unit = info.get("unit", None)

        normalized_name = normalize_column_name(col_name)
        
        columns.append(ColumnMetadata(
            name=normalized_name,
            data_type=data_type,
            unit=unit,
            description=description,
            example_values=sample_values,
            nullable=df[col_name].isna().any()
        ))
    
    return TableMetadata(
        name="sp500_companies",
        description="Financial information for S&P 500 companies including market data, fundamentals, and sector classification",
        time_granularity="Snapshot (single point in time per company)",
        row_count=len(df),
        columns=columns
    )

def normalize_column_name(name: str) -> str:
    name = name.strip().lower()
    name = re.sub(r"[^\w\s]", "_", name)   # replace /, %, etc.
    name = re.sub(r"\s+", "_", name)       # spaces → underscore
    name = re.sub(r"_+", "_", name)        # collapse underscores
    if name[0].isdigit():
        name = f"week_{name}"              # avoid leading digit
    return name


class DatabaseMetadataManager:
    """Manages database metadata for the system."""
    
    def __init__(self):
        self.table_metadata = build_sp500_metadata()
    
    def get_schema_description(self) -> str:
        """Get full schema description for LLM context."""
        return self.table_metadata.to_llm_schema()
    
    def validate_column(self, column_name: str) -> bool:
        """Validate if a column exists in the schema."""
        return self.table_metadata.get_column(column_name) is not None
    
    def get_column_info(self, column_name: str) -> Optional[ColumnMetadata]:
        """Get detailed information about a column."""
        return self.table_metadata.get_column(column_name)
    
    def get_all_columns(self) -> List[str]:
        """Get list of all column names."""
        return [col.name for col in self.table_metadata.columns]