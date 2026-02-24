"""
Migration script to add new business feature tables
CRM, Invoicing, Time Tracking, Asset Management
"""

from database.connection import get_engine, Base
from database.models import (
    # CRM Models
    CRMCustomer, CRMLead, CRMDeal, CRMActivity,
    # Invoicing Models
    Invoice, InvoiceItem, Payment,
    # Time Tracking Models
    Timesheet, TimeEntry,
    # Asset Management Models
    Asset, AssetAssignment, AssetMaintenance,
)


def migrate_business_features():
    """Create all new business feature tables"""
    print("Starting migration for business features...")

    engine = get_engine()

    # Create all tables
    Base.metadata.create_all(bind=engine)

    print("✅ Business features tables created successfully!")
    print("   - CRM Tables: crm_customers, crm_leads, crm_deals, crm_activities")
    print("   - Invoicing Tables: invoices, invoice_items, payments")
    print("   - Time Tracking Tables: timesheets, time_entries")
    print("   - Asset Management Tables: assets, asset_assignments, asset_maintenance")


if __name__ == "__main__":
    migrate_business_features()
