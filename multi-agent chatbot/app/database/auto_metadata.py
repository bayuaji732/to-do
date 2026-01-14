"""
Auto-generate metadata from actual CSV file.
"""
import pandas as pd
from pathlib import Path
from app.database.metadata import TableMetadata, ColumnMetadata, DataType


def auto_generate_metadata(csv_path: str) -> TableMetadata:
    """Auto-generate metadata from CSV file."""
    df = pd.read_csv(csv_path)
    
    columns = []
    
    for col_name in df.columns:
        # Determine data type
        dtype = df[col_name].dtype
        
        if dtype == 'object':
            data_type = DataType.STRING
        elif dtype in ['int64', 'int32']:
            data_type = DataType.INTEGER
        elif dtype in ['float64', 'float32']:
            data_type = DataType.FLOAT
        else:
            data_type = DataType.STRING
        
        # Get sample values
        sample_values = df[col_name].dropna().head(3).astype(str).tolist()
        
        # Determine unit and description based on column name
        unit = None
        description = col_name.replace('_', ' ')
        
        if 'cap' in col_name.lower():
            unit = "USD (millions)"
        elif 'price' in col_name.lower():
            unit = "USD"
        elif 'revenue' in col_name.lower() or 'income' in col_name.lower():
            unit = "USD (millions)"
        elif 'ratio' in col_name.lower():
            unit = "ratio"
        elif 'yield' in col_name.lower():
            unit = "percentage"
        
        columns.append(ColumnMetadata(
            name=col_name,
            data_type=data_type,
            unit=unit,
            description=description,
            example_values=sample_values,
            nullable=df[col_name].isna().any()
        ))
    
    return TableMetadata(
        name="sp500_companies",
        description="S&P 500 companies financial data",
        time_granularity="Snapshot",
        row_count=len(df),
        columns=columns
    )


if __name__ == "__main__":
    metadata = auto_generate_metadata("data/sp500_companies.csv")
    print(metadata.to_llm_schema())