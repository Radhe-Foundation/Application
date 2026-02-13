"""
Vernika HRA - ETL Utilities
Excel import/export and Power BI integration helpers
"""

import json
import hashlib
from database.connection import get_session
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
import warnings

# Suppress pandas warnings
warnings.filterwarnings('ignore')

# Theme colors for ETL UI
PRIMARY = "#2E86AB"
SUCCESS = "#28A745"
ERROR = "#DC3545"
WARNING = "#FFC107"
INFO = "#17A2B8"


class ETLError(Exception):
    """Custom ETL Exception"""
    pass


def get_db_session():
    """Get SQLAlchemy session (context manager)"""
    return get_session()


def hash_row_data(row_data: dict) -> str:
    """Generate hash for row data deduplication"""
    # Sort keys for consistent hashing
    sorted_data = json.dumps(row_data, sort_keys=True, default=str)
    return hashlib.sha256(sorted_data.encode()).hexdigest()


def get_table_columns(table_name: str) -> List[str]:
    """Get column names for a table using SQLAlchemy"""
    with get_db_session() as session:
        try:
            result = session.execute(f"SELECT * FROM {table_name} LIMIT 0")
            return result.keys()
        except Exception as e:
            print(f"Error getting table columns: {e}")
            return []


def get_table_data(
    table_name: str,
    columns: List[str] = None,
    limit: int = 1000,
    offset: int = 0
) -> List[Dict]:
    """Get data from a table using SQLAlchemy"""
    with get_db_session() as session:
        try:
            cols_str = ", ".join(columns) if columns else "*"
            query = f"SELECT {cols_str} FROM {table_name} LIMIT :limit OFFSET :offset"
            result = session.execute(
                query,
                {"limit": limit, "offset": offset}
            )
            rows = [dict(row) for row in result]
            return rows
        except Exception as e:
            print(f"Error getting table data: {e}")
            return []


def get_all_tables() -> List[str]:
    """Get all table names in the database using SQLAlchemy"""
    with get_db_session() as session:
        try:
            result = session.execute(
                "SELECT table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY table_name"
            )
            tables = [row[0] for row in result]
            return tables
        except Exception as e:
            print(f"Error getting tables: {e}")
            return []


# ==================== EXCEL IMPORT FUNCTIONS ====================

def read_excel_file(file_path: str) -> Tuple[pd.DataFrame, List[str]]:
    """
    Read Excel file and return DataFrame with column names

    Args:
        file_path: Path to Excel file

    Returns:
        Tuple of (DataFrame, list of column names)
    """
    try:
        # Try reading with openpyxl engine
        df = pd.read_excel(file_path, engine='openpyxl')
        # Clean column names (remove whitespace, standardize)
        df.columns = [str(col).strip() for col in df.columns]
        return df, list(df.columns)
    except Exception as e:
        raise ETLError(f"Failed to read Excel file: {e}")


def preview_excel_data(file_path: str, rows: int = 5) -> List[Dict]:
    """
    Preview first N rows of Excel file

    Args:
        file_path: Path to Excel file
        rows: Number of rows to preview

    Returns:
        List of dictionaries representing rows
    """
    try:
        df = pd.read_excel(file_path, engine='openpyxl', nrows=rows)
        df.columns = [str(col).strip() for col in df.columns]
        # Convert to records with serializable types
        records = []
        for _, row in df.iterrows():
            record = {}
            for col in df.columns:
                val = row[col]
                if isinstance(val, pd.Timestamp):
                    record[col] = val.strftime('%Y-%m-%d')
                elif isinstance(val, (pd.Timedelta,)):
                    record[col] = str(val)
                elif pd.isna(val):
                    record[col] = None
                else:
                    record[col] = val
            records.append(record)
        return records
    except Exception as e:
        raise ETLError(f"Failed to preview Excel data: {e}")


def get_excel_sheet_names(file_path: str) -> List[str]:
    """Get sheet names from Excel file"""
    try:
        xl = pd.ExcelFile(file_path, engine='openpyxl')
        return xl.sheet_names
    except Exception as e:
        raise ETLError(f"Failed to get sheet names: {e}")


def import_excel_to_db(
    file_path: str,
    table_name: str,
    column_mapping: Dict[str, str],
    header_row: int = 0,
    skip_rows: int = 0
) -> Dict[str, int]:
    """
    Import Excel data to database table

    Args:
        file_path: Path to Excel file
        table_name: Target database table
        column_mapping: Dict mapping Excel columns to DB columns
        header_row: Row number containing headers
        skip_rows: Number of rows to skip

    Returns:
        Dict with success_count, error_count, total_count
    """
    with get_db_session() as session:
        cursor = session.connection().connection.cursor()

    result = {
        'total_count': 0,
        'success_count': 0,
        'error_count': 0,
        'errors': []
    }

    try:
        # Read Excel data
        df = pd.read_excel(file_path, engine='openpyxl',
                           header=header_row, skiprows=skip_rows)
        df.columns = [str(col).strip() for col in df.columns]

        # Filter to mapped columns only
        db_columns = list(column_mapping.values())
        excel_columns = list(column_mapping.keys())

        # Get DB table columns
        # Use SQLAlchemy reflection for column info
        from sqlalchemy import inspect
        inspector = inspect(session.bind)
        db_cols_info = {col['name']
            : col for col in inspector.get_columns(table_name)}

        # Filter to valid columns
        valid_mappings = {}
        for excel_col, db_col in column_mapping.items():
            if db_col in db_cols_info and excel_col in df.columns:
                valid_mappings[excel_col] = db_col

        if not valid_mappings:
            raise ETLError("No valid column mappings found")

        # Get the columns that exist in both Excel and DB
        valid_db_cols = [db_col for db_col in valid_mappings.values()]

        # Prepare insert statement
        placeholders = ", ".join(["?"] * len(valid_db_cols))
        insert_sql = f"INSERT OR REPLACE INTO {table_name} ({', '.join(valid_db_cols)}) VALUES ({placeholders})"

        # Process each row
        for idx, row in df.iterrows():
            try:
                result['total_count'] += 1

                # Prepare values
                values = []
                for db_col in valid_db_cols:
                    excel_col = [
                        k for k, v in valid_mappings.items() if v == db_col][0]
                    val = row[excel_col]

                    # Handle different data types
                    if pd.isna(val):
                        values.append(None)
                    elif isinstance(val, pd.Timestamp):
                        values.append(val.strftime('%Y-%m-%d'))
                    elif isinstance(val, (int, float, str)):
                        values.append(val)
                    else:
                        values.append(str(val))

                # Execute insert
                cursor.execute(insert_sql, values)
                result['success_count'] += 1

            except Exception as row_error:
                result['error_count'] += 1
                result['errors'].append(f"Row {idx + 1}: {str(row_error)}")

        session.commit()

    except Exception as e:
        result['errors'].append(f"Import failed: {str(e)}")
        raise ETLError(f"Import failed: {e}")
    finally:
        session.close()

    return result


# ==================== EXCEL EXPORT FUNCTIONS ====================

def export_table_to_excel(
    table_name: str,
    output_path: str,
    columns: List[str] = None,
    query: str = None
) -> Dict[str, Any]:
    """
    Export table data to Excel file

    Args:
        table_name: Source table name
        output_path: Output Excel file path
        columns: List of columns to export (None for all)
        query: Custom query instead of table name

    Returns:
        Dict with file_path, row_count
    """
    with get_db_session() as session:
        engine = session.bind
        if query:
            df = pd.read_sql_query(query, engine)
        else:
            cols_str = ", ".join(columns) if columns else "*"
            df = pd.read_sql_query(
                f"SELECT {cols_str} FROM {table_name}", engine)
        # Convert datetime columns
        for col in df.columns:
            if df[col].dtype == 'object':
                # Try to convert datetime strings
                try:
                    df[col] = pd.to_datetime(df[col], errors='coerce')
                except Exception:
                    pass

        # Export to Excel
        df.to_excel(output_path, index=False, engine='openpyxl')

        return {
            'file_path': output_path,
            'row_count': len(df),
            'column_count': len(df.columns),
            'columns': list(df.columns)
        }

    except Exception as e:
        raise ETLError(f"Export failed: {e}")
    # No explicit close needed for SQLAlchemy session here


def export_custom_query_to_excel(
    query: str,
    output_path: str,
    sheet_name: str = "Data"
) -> Dict[str, Any]:
    """
    Export custom query results to Excel

    Args:
        query: SQL query to execute
        output_path: Output Excel file path
        sheet_name: Name for the worksheet

    Returns:
        Dict with file_path, row_count
    """
    with get_db_session() as session:
        engine = session.bind
        df = pd.read_sql_query(query, engine)

        # Process datetime columns
        for col in df.columns:
            if df[col].dtype == 'object':
                try:
                    df[col] = pd.to_datetime(df[col], errors='coerce')
                except Exception:
                    pass

        # Export with multiple sheets support
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name=sheet_name, index=False)

        return {
            'file_path': output_path,
            'row_count': len(df),
            'column_count': len(df.columns),
            'sheet_name': sheet_name
        }

    except Exception as e:
        raise ETLError(f"Export failed: {e}")
    # No explicit close needed for SQLAlchemy session here


# ==================== POWER BI INTEGRATION ====================

class PowerBIClient:
    """
    Power BI REST API Client for dataset refresh operations
    Note: This is a mock implementation. Actual Power BI integration
    requires Azure AD authentication and proper API setup.
    """

    def __init__(
        self,
        tenant_id: str = "",
        client_id: str = "",
        client_secret: str = "",
        workspace_id: str = ""
    ):
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.workspace_id = workspace_id
        self.access_token = None
        self.is_connected = False

    def authenticate(self) -> bool:
        """
        Authenticate with Azure AD for Power BI API access

        Returns:
            True if authenticated successfully
        """
        # Mock authentication - in production, use MSAL library
        if self.tenant_id and self.client_id and self.client_secret:
            # Actual implementation would use:
            # from msal import ConfidentialClientApplication
            # app = ConfidentialClientApplication(...)
            self.access_token = "mock_token"
            self.is_connected = True
            return True
        else:
            # Return True for demo purposes
            self.is_connected = True
            return True

    def get_workspaces(self) -> List[Dict]:
        """Get list of Power BI workspaces"""
        # Mock workspaces for demo
        return [
            {
                "id": "ws-001",
                "name": "HR Analytics Workspace",
                "type": "Workspace",
                "state": "Active"
            },
            {
                "id": "ws-002",
                "name": "Executive Dashboard",
                "type": "Workspace",
                "state": "Active"
            }
        ]

    def get_datasets(self, workspace_id: str = None) -> List[Dict]:
        """Get list of datasets in a workspace"""
        ws_id = workspace_id or self.workspace_id
        # Mock datasets for demo
        return [
            {
                "id": "ds-001",
                "name": "Employee Analytics Dataset",
                "configured_by": "admin@vernika.com",
                "is_refreshable": True,
                "web_url": f"https://app.powerbi.com/datasets/ds-001"
            },
            {
                "id": "ds-002",
                "name": "Attendance Dashboard Dataset",
                "configured_by": "admin@vernika.com",
                "is_refreshable": True,
                "web_url": f"https://app.powerbi.com/datasets/ds-002"
            },
            {
                "id": "ds-003",
                "name": "Performance Metrics Dataset",
                "configured_by": "admin@vernika.com",
                "is_refreshable": True,
                "web_url": f"https://app.powerbi.com/datasets/ds-003"
            }
        ]

    def refresh_dataset(
        self,
        dataset_id: str,
        refresh_type: str = "full"
    ) -> Dict:
        """
        Trigger dataset refresh

        Args:
            dataset_id: ID of dataset to refresh
            refresh_type: 'full' or 'incremental'

        Returns:
            Dict with refresh status
        """
        # Mock refresh for demo
        return {
            "id": f"refresh-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "dataset_id": dataset_id,
            "refresh_type": refresh_type,
            "status": "completed",
            "start_time": datetime.now().isoformat(),
            "end_time": datetime.now().isoformat()
        }

    def get_refresh_history(self, dataset_id: str) -> List[Dict]:
        """Get refresh history for a dataset"""
        # Mock history for demo
        return [
            {
                "id": "refresh-001",
                "refresh_type": "full",
                "status": "Completed",
                "start_time": "2024-03-10T10:00:00",
                "end_time": "2024-03-10T10:05:00"
            },
            {
                "id": "refresh-002",
                "refresh_type": "full",
                "status": "Completed",
                "start_time": "2024-03-09T10:00:00",
                "end_time": "2024-03-09T10:04:00"
            }
        ]

    def get_dataset_details(self, dataset_id: str) -> Dict:
        """Get detailed information about a dataset"""
        datasets = self.get_datasets()
        for ds in datasets:
            if ds['id'] == dataset_id:
                return ds
        return {}


def get_powerbi_client() -> PowerBIClient:
    """Get Power BI client instance"""
    return PowerBIClient()


# ==================== DATA TRANSFORMATION UTILITIES ====================

def normalize_column_name(name: str) -> str:
    """Normalize column name for consistent mapping"""
    # Convert to lowercase, replace spaces with underscores
    return name.lower().strip().replace(' ', '_')


def get_column_suggestions(
    excel_columns: List[str],
    db_columns: List[str]
) -> Dict[str, str]:
    """
    Suggest column mappings based on name similarity

    Args:
        excel_columns: List of Excel column names
        db_columns: List of database column names

    Returns:
        Dict mapping Excel columns to suggested DB columns
    """
    suggestions = {}

    for excel_col in excel_columns:
        excel_normalized = normalize_column_name(excel_col)

        # Try exact match first
        for db_col in db_columns:
            if normalize_column_name(db_col) == excel_normalized:
                suggestions[excel_col] = db_col
                break
        else:
            # Try partial match
            for db_col in db_columns:
                if excel_normalized in normalize_column_name(db_col) or \
                   normalize_column_name(db_col) in excel_normalized:
                    suggestions[excel_col] = db_col
                    break

    return suggestions


def validate_data_types(
    df: pd.DataFrame,
    table_name: str
) -> Dict[str, List[str]]:
    """
    Validate data types in DataFrame against table schema

    Args:
        df: DataFrame to validate
        table_name: Target table name

    Returns:
        Dict with 'errors' and 'warnings' lists
    """
    result = {'errors': [], 'warnings': []}

    with get_db_session() as session:
        cursor = session.connection().connection.cursor()

    try:
        # Use SQLAlchemy reflection for column info
        from sqlalchemy import inspect
        inspector = inspect(session.bind)
        schema = {col['name']
            : col for col in inspector.get_columns(table_name)}

        for col in df.columns:
            if col in schema:
                col_info = schema[col]
                dtype = col_info['type'].upper() if col_info['type'] else ''

                # Check for nullability
                if col_info['notnull'] and df[col].isna().any():
                    result['warnings'].append(
                        f"Column '{col}' has NOT NULL constraint but contains null values"
                    )

                # Type-specific validation
                if 'INT' in dtype:
                    non_numeric = df[col][pd.to_numeric(
                        df[col], errors='coerce').isna() & df[col].notna()]
                    if len(non_numeric) > 0:
                        result['errors'].append(
                            f"Column '{col}' should be numeric but contains non-numeric values"
                        )
                elif 'DATE' in dtype:
                    try:
                        pd.to_datetime(df[col], errors='raise')
                    except Exception:
                        result['warnings'].append(
                            f"Column '{col}' may not be in valid date format"
                        )

    # No explicit close needed for SQLAlchemy session here

    return result


# ==================== EXPORT/IMPORT SUMMARY ====================

def get_import_templates() -> List[Dict]:
    """Get available import templates"""
    return [
        {
            "id": "employees",
            "name": "Employee Import",
            "description": "Import employee records from Excel",
            "target_table": "employees",
            "required_columns": ["employee_code", "first_name", "last_name", "email"],
            "optional_columns": ["phone", "date_of_joining", "basic_salary"]
        },
        {
            "id": "departments",
            "name": "Department Import",
            "description": "Import department records from Excel",
            "target_table": "departments",
            "required_columns": ["name", "code"],
            "optional_columns": ["description"]
        },
        {
            "id": "attendances",
            "name": "Attendance Import",
            "description": "Import attendance records from Excel",
            "target_table": "attendances",
            "required_columns": ["employee_id", "date", "status"],
            "optional_columns": ["check_in", "check_out", "working_hours"]
        },
        {
            "id": "tasks",
            "name": "Task Import",
            "description": "Import task records from Excel",
            "target_table": "tasks",
            "required_columns": ["title", "assigned_to_id"],
            "optional_columns": ["description", "priority", "status", "due_date"]
        }
    ]


def get_export_options() -> List[Dict]:
    """Get available export options"""
    return [
        {
            "id": "employees",
            "name": "Employees",
            "description": "Export all employee data",
            "table": "employees",
            "columns": None  # All columns
        },
        {
            "id": "departments",
            "name": "Departments",
            "description": "Export all department data",
            "table": "departments",
            "columns": None
        },
        {
            "id": "attendances",
            "name": "Attendance",
            "description": "Export attendance records",
            "table": "attendances",
            "columns": None
        },
        {
            "id": "tasks",
            "name": "Tasks",
            "description": "Export task records",
            "table": "tasks",
            "columns": None
        },
        {
            "id": "leave_requests",
            "name": "Leave Requests",
            "description": "Export leave request data",
            "table": "leave_requests",
            "columns": None
        }
    ]
