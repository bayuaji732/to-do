"""
Database metadata management for schema-aware querying.
"""
from dataclasses import dataclass
from typing import List, Dict, Optional
from enum import Enum


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
        for col in self.columns:
            if col.name.lower() == name.lower():
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
    """
    Build metadata for S&P 500 dataset.
    This should be constructed after inspecting the actual dataset.
    """
    return TableMetadata(
        name="sp500_companies",
        description="Financial information for S&P 500 companies including market data, fundamentals, and sector classification",
        time_granularity="Snapshot (single point in time per company)",
        row_count=503,  # Approximate, update after loading
        columns=[
            ColumnMetadata(
                name="Symbol",
                data_type=DataType.STRING,
                unit=None,
                description="Stock ticker symbol",
                example_values=["AAPL", "MSFT", "GOOGL"],
                nullable=False
            ),
            ColumnMetadata(
                name="Security",
                data_type=DataType.STRING,
                unit=None,
                description="Company name or security description",
                example_values=["Apple Inc.", "Microsoft Corporation"],
                nullable=False
            ),
            ColumnMetadata(
                name="Sector",
                data_type=DataType.STRING,
                unit=None,
                description="GICS sector classification",
                example_values=["Information Technology", "Health Care", "Financials"],
                nullable=False
            ),
            ColumnMetadata(
                name="Sub_Industry",
                data_type=DataType.STRING,
                unit=None,
                description="GICS sub-industry classification",
                example_values=["Technology Hardware, Storage & Peripherals", "Pharmaceuticals"],
                nullable=True
            ),
            ColumnMetadata(
                name="Headquarters_Location",
                data_type=DataType.STRING,
                unit=None,
                description="City and state of company headquarters",
                example_values=["Cupertino, California", "Redmond, Washington"],
                nullable=True
            ),
            ColumnMetadata(
                name="Date_added",
                data_type=DataType.DATE,
                unit=None,
                description="Date when company was added to S&P 500 index",
                example_values=["1982-11-30", "1994-06-01"],
                nullable=True
            ),
            ColumnMetadata(
                name="CIK",
                data_type=DataType.INTEGER,
                unit=None,
                description="Central Index Key (SEC identifier)",
                example_values=["320193", "789019"],
                nullable=True
            ),
            ColumnMetadata(
                name="Founded",
                data_type=DataType.STRING,
                unit=None,
                description="Year company was founded",
                example_values=["1976", "1975"],
                nullable=True
            ),
            ColumnMetadata(
                name="Market_Cap",
                data_type=DataType.FLOAT,
                unit="USD (millions)",
                description="Market capitalization",
                example_values=["2800000", "2400000"],
                nullable=True
            ),
            ColumnMetadata(
                name="Price",
                data_type=DataType.FLOAT,
                unit="USD",
                description="Current stock price",
                example_values=["178.25", "380.50"],
                nullable=True
            ),
            ColumnMetadata(
                name="Revenue",
                data_type=DataType.FLOAT,
                unit="USD (millions)",
                description="Annual revenue",
                example_values=["394328", "211915"],
                nullable=True
            ),
            ColumnMetadata(
                name="Net_Income",
                data_type=DataType.FLOAT,
                unit="USD (millions)",
                description="Annual net income",
                example_values=["99803", "72361"],
                nullable=True
            ),
            ColumnMetadata(
                name="Employees",
                data_type=DataType.INTEGER,
                unit="count",
                description="Number of employees",
                example_values=["164000", "221000"],
                nullable=True
            ),
            ColumnMetadata(
                name="PE_Ratio",
                data_type=DataType.FLOAT,
                unit="ratio",
                description="Price-to-Earnings ratio",
                example_values=["28.5", "32.1"],
                nullable=True
            ),
            ColumnMetadata(
                name="Dividend_Yield",
                data_type=DataType.FLOAT,
                unit="percentage",
                description="Annual dividend yield as percentage",
                example_values=["0.52", "0.75"],
                nullable=True
            ),
        ]
    )


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