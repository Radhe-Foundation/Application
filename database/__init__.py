"""
Central Database Module - Model Registry & Safe Imports
Prevents circular import issues across CRM screens/repos
"""

# Force model registry order to prevent circular imports
try:
    from database.connection import Base
    from database.models import (
        User, Employee, Lead, Contact, CalendarEvent, Supplier,
        Warehouse, Asset, Contract, Invoice, InvoiceItem
    )
except ImportError as e:
    print(f"Model import warning (safe): {e}")

# Export key symbols for safe imports
__all__ = [
    'Base', 'engine', 'User', 'Employee', 'Lead', 'Contact',
    'CalendarEvent', 'Supplier', 'Warehouse', 'Asset',
    'Contract', 'Invoice', 'InvoiceItem'
]

# Verify critical CRM models available


def verify_crm_models():
    """Verify CRM models are registered (called by fix script)"""
    required = ['User', 'Lead', 'Contact']
    missing = []
    for model in required:
        if model not in globals():
            missing.append(model)
    if missing:
        raise ImportError(f"Missing CRM models: {missing}")
    print("✅ All CRM models registered successfully")
