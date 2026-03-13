#!/usr/bin/env python3
"""
CRM Import Fix & Test Data Script
- Verifies model registry (fixes circular import User error)
- Creates test data if tables empty
- Run: python scripts/fix_crm_imports.py
"""

from database import verify_crm_models
from database.crm_repository import crm_repo as crm_repo_import
from database.session_manager import get_session
import logging
# Path fix for script execution
import sys
import os
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, base_dir)

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Main fix function - run model verification + test data."""
    print("🔧 Running CRM Import Fix...")

    try:
        # 1. Verify model registry
        print("1. Verifying CRM models...")
        verify_crm_models()
        print("✅ Models OK")

        # 2. Check if data exists
        print("2. Checking existing data...")
        with get_session() as session:
            from database.models import Lead
            lead_count = session.query(Lead).count()
            print(f"   Leads: {lead_count}")

            if lead_count == 0:
                print("   → No data found. Creating test data...")
                result = crm_repo_import.create_test_data()
                total = sum(result.values())
                print(f"✅ Created {total} records: {result}")
            else:
                print("   Data exists - skipping test data")

    except Exception as e:
        logger.error(f"❌ Fix failed: {e}")
        raise

    print("🎉 CRM Fix complete! Run app and test CRM screen.")


if __name__ == "__main__":
    main()
