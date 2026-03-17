"""
RadheFoundation HRA - Google Sheets Integration
Export data to Google Sheets for cloud collaboration.
"""

import os
from datetime import datetime
from typing import Dict, List, Optional
from abc import ABC, abstractmethod


class GoogleSheetsExporter:
    """
    Export data to Google Sheets format.

    Note: This requires Google Sheets API credentials.
    For production use, set up Google Cloud Console and install:
    pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client

    For now, this provides a compatibility layer that:
    1. Formats data for Google Sheets import
    2. Generates shareable links format
    3. Prepares data for API integration
    """

    def __init__(self):
        self.sheets_url_format = "https://docs.google.com/spreadsheets/d/{sheet_id}/edit"
        self.api_prefix = "/api/v1/sheets"

    def prepare_data_for_sheets(
        self,
        headers: List[str],
        rows: List[List],
        sheet_name: str = "Data"
    ) -> Dict:
        """
        Prepare data in Google Sheets import format.

        Args:
            headers: Column headers
            rows: Data rows
            sheet_name: Name of the sheet

        Returns:
            Dictionary ready for Google Sheets API
        """
        return {
            "properties": {
                "title": sheet_name,
                "locale": "en_US",
                "spreadsheetTimezone": "Asia/Kolkata",
            },
            "sheets": [{
                "properties": {
                    "title": sheet_name,
                    "index": 0,
                },
                "data": [{
                    "rowData": self._format_row_data(headers, rows)
                }]
            }]
        }

    def _format_row_data(
        self,
        headers: List[str],
        rows: List[List]
    ) -> List[Dict]:
        """
        Format data as Google Sheets rowData format.

        Args:
            headers: Column headers
            rows: Data rows

        Returns:
            List of row data dictionaries
        """
        row_data = []

        # Add header row
        header_row = {
            "values": [
                {"formattedValue": str(header), "effectiveValue": {
                    "stringValue": header}}
                for header in headers
            ]
        }
        row_data.append(header_row)

        # Add data rows
        for row in rows:
            values = []
            for cell in row:
                if isinstance(cell, (int, float)):
                    values.append({
                        "formattedValue": str(cell),
                        "effectiveValue": {"numberValue": float(cell)}
                    })
                elif cell is None:
                    values.append({"formattedValue": ""})
                else:
                    values.append({
                        "formattedValue": str(cell),
                        "effectiveValue": {"stringValue": str(cell)}
                    })

            row_data.append({"values": values})

        return row_data

    def generate_sheets_import_format(
        self,
        data: Dict[str, List[Dict]],
        filename: str = "RadheFoundation_export"
    ) -> str:
        """
        Generate data in a format easily imported to Google Sheets.
        Returns CSV-formatted string with sheet names.

        Args:
            data: Dictionary with sheet names as keys and list of dicts as values
            filename: Base filename

        Returns:
            Formatted string ready for Google Sheets
        """
        output_parts = []

        for sheet_name, rows in data.items():
            if not rows:
                continue

            # Add sheet separator
            output_parts.append(f"=== {sheet_name} ===")
            output_parts.append("")

            # Get headers from first row
            headers = list(rows[0].keys())
            output_parts.append(",".join(headers))

            # Add data rows
            for row in rows:
                values = []
                for header in headers:
                    value = row.get(header, "")
                    # Escape commas and quotes
                    if isinstance(value, str):
                        value = value.replace('"', '""')
                    values.append(f'"{value}"')
                output_parts.append(",".join(values))

            output_parts.append("")

        return "\n".join(output_parts)

    def get_sync_config(self) -> Dict:
        """
        Get configuration for Google Sheets sync.

        Returns:
            Configuration dictionary for sync setup
        """
        return {
            "version": "1.0",
            "last_updated": datetime.now().isoformat(),
            "tables": [
                {
                    "name": "employees",
                    "sync_mode": "full",  # full or incremental
                    "key_column": "id",
                    "order_column": "id",
                    "columns": [
                        "id", "employee_code", "first_name", "last_name",
                        "email", "phone", "department", "position",
                        "employment_type", "employment_status",
                        "date_of_joining", "is_active", "created_at"
                    ]
                },
                {
                    "name": "departments",
                    "sync_mode": "full",
                    "key_column": "id",
                    "order_column": "id",
                    "columns": [
                        "id", "name", "code", "description",
                        "budget", "location", "head_name", "created_at"
                    ]
                },
                {
                    "name": "positions",
                    "sync_mode": "full",
                    "key_column": "id",
                    "order_column": "id",
                    "columns": [
                        "id", "code", "title", "description",
                        "department", "min_salary", "max_salary", "is_active"
                    ]
                },
                {
                    "name": "attendances",
                    "sync_mode": "incremental",
                    "key_column": "id",
                    "order_column": "date",
                    "columns": [
                        "id", "employee_code", "employee_name", "department",
                        "date", "check_in", "check_out", "status", "working_hours"
                    ]
                },
                {
                    "name": "leave_requests",
                    "sync_mode": "incremental",
                    "key_column": "id",
                    "order_column": "created_at",
                    "columns": [
                        "id", "employee_name", "department",
                        "start_date", "end_date", "days_requested",
                        "reason", "status", "created_at"
                    ]
                }
            ],
            "google_sheets": {
                "required_scopes": [
                    "https://www.googleapis.com/auth/spreadsheets",
                    "https://www.googleapis.com/auth/drive.file"
                ],
                "api_version": "v4",
                "batch_update": True
            }
        }

    def create_sync_script_template(self) -> str:
        """
        Create a template script for Google Sheets sync.

        Returns:
            Python script template for sync
        """
        return '''#!/usr/bin/env python3
"""
RadheFoundation HRA - Google Sheets Sync Script
Generated template for syncing data to Google Sheets.

Instructions:
1. Install required packages:
   pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client

2. Set up Google Cloud Console:
   - Create a project
   - Enable Google Sheets API and Google Drive API
   - Create OAuth 2.0 credentials
   - Download credentials.json

3. Configure environment variables:
   export GOOGLE_CREDENTIALS_PATH="/path/to/credentials.json"
   export SPREADSHEET_ID="your_spreadsheet_id"

4. Run the script
"""

import os
import json
from datetime import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


class RadheFoundationSheetsSync:
    """Sync RadheFoundation data to Google Sheets"""
    
    SCOPES = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive.file'
    ]
    
    def __init__(self, credentials_path: str = None, spreadsheet_id: str = None):
        self.credentials_path = credentials_path or os.environ.get(
            'GOOGLE_CREDENTIALS_PATH', 'credentials.json'
        )
        self.spreadsheet_id = spreadsheet_id or os.environ.get(
            'SPREADSHEET_ID', ''
        )
        self.creds = None
        self.service = None
    
    def authenticate(self):
        """Authenticate with Google API"""
        self.creds = None
        
        if os.path.exists('token.json'):
            self.creds = Credentials.from_authorized_user_file(
                'token.json', self.SCOPES)
        
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, self.SCOPES)
                self.creds = flow.run_local_server(port=0)
            
            with open('token.json', 'w') as token:
                token.write(self.creds.to_json())
        
        self.service = build('sheets', 'v4', credentials=self.creds)
        print("✓ Authenticated with Google Sheets API")
    
    def create_spreadsheet(self, title: str) -> str:
        """Create a new spreadsheet"""
        spreadsheet = {
            'properties': {
                'title': title,
                'locale': 'en_US',
                'spreadsheetTimezone': 'Asia/Kolkata',
            }
        }
        
        spreadsheet = self.service.spreadsheets().create(
            body=spreadsheet,
            fields='spreadsheetId'
        ).execute()
        
        print(f"✓ Created spreadsheet: {spreadsheet['spreadsheetId']}")
        return spreadsheet['spreadsheetId']
    
    def write_data(
        self,
        sheet_id: str,
        range_name: str,
        values: List[List]
    ):
        """Write data to a sheet"""
        body = {
            'values': values
        }
        
        result = self.service.spreadsheets().values().update(
            spreadsheetId=sheet_id,
            range=range_name,
            valueInputOption='RAW',
            body=body
        ).execute()
        
        print(f"✓ Wrote {result.get('updatedCells')} cells to {range_name}")
        return result
    
    def sync_employees(self, sheet_id: str):
        """Sync employees data"""
        from utils.excel_export import get_exporter
        exporter = get_exporter()
        csv_data = exporter.export_employees()
        
        # Parse CSV to list of lists
        rows = [line.split(',') for line in csv_data.split('\\n') if line]
        
        self.write_data(sheet_id, 'Employees!A1', rows)
    
    def sync_all(self):
        """Sync all data to Google Sheets"""
        if not self.spreadsheet_id:
            self.spreadsheet_id = self.create_spreadsheet(
                f'RadheFoundation HRA Export - {datetime.now().strftime("%Y-%m-%d")}'
            )
        
        print("\\nSyncing data...")
        
        try:
            self.sync_employees(self.spreadsheet_id)
            print("\\n✓ All data synced successfully!")
            print(f"\\nSpreadsheet URL: https://docs.google.com/spreadsheets/d/{self.spreadsheet_id}")
        except Exception as e:
            print(f"\\n✗ Sync failed: {e}")
            raise


def main():
    sync = RadheFoundationSheetsSync()
    
    # Authenticate
    sync.authenticate()
    
    # Sync all data
    sync.sync_all()


if __name__ == "__main__":
    main()
'''


class CloudDatabaseConfig:
    """
    Configuration for cloud database connections.
    Supports PostgreSQL, MySQL, and Google Cloud SQL.
    """

    # Environment variable names
    ENV_VARS = {
        'postgresql': {
            'host': 'DB_HOST',
            'port': 'DB_PORT',
            'database': 'DB_NAME',
            'user': 'DB_USER',
            'password': 'DB_PASSWORD',
            'ssl': 'DB_SSL_MODE',
        },
        'mysql': {
            'host': 'MYSQL_HOST',
            'port': 'MYSQL_PORT',
            'database': 'MYSQL_DATABASE',
            'user': 'MYSQL_USER',
            'password': 'MYSQL_PASSWORD',
            'ssl': 'MYSQL_SSL_MODE',
        },
        'gcp': {
            'project': 'GCP_PROJECT',
            'instance': 'CLOUD_SQL_INSTANCE',
            'database': 'CLOUD_SQL_DATABASE',
            'user': 'CLOUD_SQL_USER',
            'password': 'CLOUD_SQL_PASSWORD',
            'connection_name': 'CLOUD_SQL_CONNECTION',
        }
    }

    @classmethod
    def get_postgresql_config(cls) -> Dict:
        """Get PostgreSQL configuration from environment"""
        import os
        return {
            'host': os.environ.get(cls.ENV_VARS['postgresql']['host'], 'localhost'),
            'port': int(os.environ.get(cls.ENV_VARS['postgresql']['port'], 5432)),
            'database': os.environ.get(cls.ENV_VARS['postgresql']['database'], 'RadheFoundation'),
            'user': os.environ.get(cls.ENV_VARS['postgresql']['user'], 'postgres'),
            'password': os.environ.get(cls.ENV_VARS['postgresql']['password'], ''),
            'sslmode': os.environ.get(cls.ENV_VARS['postgresql']['ssl'], 'prefer'),
        }

    @classmethod
    def get_mysql_config(cls) -> Dict:
        """Get MySQL configuration from environment"""
        import os
        return {
            'host': os.environ.get(cls.ENV_VARS['mysql']['host'], 'localhost'),
            'port': int(os.environ.get(cls.ENV_VARS['mysql']['port'], 3306)),
            'database': os.environ.get(cls.ENV_VARS['mysql']['database'], 'RadheFoundation'),
            'user': os.environ.get(cls.ENV_VARS['mysql']['user'], 'root'),
            'password': os.environ.get(cls.ENV_VARS['mysql']['password'], ''),
        }

    @classmethod
    def get_database_url(cls, db_type: str = 'sqlite') -> str:
        """
        Get database URL for SQLAlchemy.

        Args:
            db_type: 'sqlite', 'postgresql', 'mysql'

        Returns:
            Database URL string
        """
        if db_type == 'sqlite':
            return 'sqlite:///RadheFoundation.db'
        elif db_type == 'postgresql':
            config = cls.get_postgresql_config()
            return (
                f"postgresql://{config['user']}:{config['password']}"
                f"@{config['host']}:{config['port']}/{config['database']}"
            )
        elif db_type == 'mysql':
            config = cls.get_mysql_config()
            return (
                f"mysql+pymysql://{config['user']}:{config['password']}"
                f"@{config['host']}:{config['port']}/{config['database']}"
            )
        else:
            raise ValueError(f"Unsupported database type: {db_type}")

    @classmethod
    def get_sync_config(cls) -> Dict:
        """Get cloud sync configuration"""
        return {
            'postgresql': cls.get_postgresql_config(),
            'mysql': cls.get_mysql_config(),
            'gcp': {
                'project': os.environ.get('GCP_PROJECT', ''),
                'instance': os.environ.get('CLOUD_SQL_INSTANCE', ''),
            },
            'google_sheets': {
                'enabled': True,
                'sync_interval': '1h',  # Sync every hour
                'auto_export': False,
            }
        }


def get_google_sheets_exporter() -> GoogleSheetsExporter:
    """Get Google Sheets exporter instance"""
    return GoogleSheetsExporter()


if __name__ == "__main__":
    exporter = get_google_sheets_exporter()

    print("Google Sheets Integration Configuration")
    print("=" * 50)
    print()

    # Print sync configuration
    config = exporter.get_sync_config()
    print("Sync Configuration:")
    print(json.dumps(config, indent=2))
    print()

    # Print sync script template path
    script = exporter.create_sync_script_template()
    with open('sync_to_sheets.py', 'w') as f:
        f.write(script)
    print(f"Sync script template saved to: sync_to_sheets.py")
    print()

    print("To use Google Sheets integration:")
    print("1. Install required packages:")
    print("   pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client")
    print()
    print("2. Set up Google Cloud Console:")
    print("   - Enable Google Sheets API and Google Drive API")
    print("   - Create OAuth 2.0 credentials")
    print()
    print("3. Run sync_to_sheets.py")
