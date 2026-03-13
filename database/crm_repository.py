# Vernika CRM Repository - Optimized CRM Operations

import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta, date
from functools import lru_cache

from sqlalchemy.orm import Session, joinedload

from database.session_manager import get_session
from database.repositories import BaseRepository
from database import Lead, Contact, CalendarEvent, Supplier, Warehouse, Asset, Contract, Invoice
from database.models import User

logger = logging.getLogger(__name__)


class CRMRRepository(BaseRepository):
    "Dedicated CRM repository with caching and optimizations."

    @classmethod
    @lru_cache(maxsize=128)
    def get_all_leads_cached(cls, limit: int = 50) -> List[Lead]:
        "Get all leads with cache."
        return cls.get_all_leads(limit=limit)

    @classmethod
    def get_all_leads(cls, limit: int = 50) -> List[Lead]:
        "Get all leads."
        with get_session() as session:
            try:
                return (session.query(Lead)
                        .options(joinedload(Lead.assigned_to))
                        .order_by(Lead.created_at.desc())
                        .limit(limit)
                        .all())
            except Exception as e:
                logger.error(f"Leads query error: {e}")
                return []

    @classmethod
    def get_all_contacts(cls, limit: int = 50) -> List[Contact]:
        "Get all contacts."
        with get_session() as session:
            try:
                return (session.query(Contact)
                        .order_by(Contact.created_at.desc())
                        .limit(limit)
                        .all())
            except Exception as e:
                logger.error(f"Contacts query error: {e}")
                return []

    @classmethod
    def get_all_events(cls, limit: int = 100, user_id: Optional[int] = None) -> List[CalendarEvent]:
        "Get all events (increased limit, optional user filter). "
        with get_session() as session:
            try:
                query = (session.query(CalendarEvent)
                         .options(joinedload(CalendarEvent.lead),
                                  joinedload(CalendarEvent.contact),
                                  joinedload(CalendarEvent.related_contract),
                                  joinedload(CalendarEvent.related_invoice))
                         .order_by(CalendarEvent.start_time.desc()))

                if user_id:
                    query = query.filter(CalendarEvent.organizer_id == user_id)

                if limit:
                    query = query.limit(limit)

                return query.all()
            except Exception as e:
                logger.error(f"Events query error: {e}")
                return []

    @classmethod
    def get_events_by_date_range(cls, start_date: date, end_date: Optional[date] = None, user_id: Optional[int] = None) -> List[CalendarEvent]:
        "Get events within date range for calendar."
        if end_date is None:
            end_date = start_date

        with get_session() as session:
            try:
                query = (session.query(CalendarEvent)
                         .options(joinedload(CalendarEvent.lead),
                                  joinedload(CalendarEvent.contact),
                                  joinedload(CalendarEvent.related_contract),
                                  joinedload(CalendarEvent.related_invoice))
                         .filter(CalendarEvent.start_time >= datetime.combine(start_date, datetime.min.time()))
                         .filter(CalendarEvent.start_time <= datetime.combine(end_date, datetime.max.time())))

                if user_id:
                    query = query.filter(CalendarEvent.organizer_id == user_id)

                return query.order_by(CalendarEvent.start_time).all()
            except Exception as e:
                logger.error(f"Date range events error: {e}")
                return []

    @classmethod
    @lru_cache(maxsize=1)
    def refresh_events_cache(cls):
        "Clear events cache."
        cls.get_all_events.cache_clear()

    @classmethod
    def get_all_vendors(cls, limit: int = 50) -> List[Supplier]:
        "Get all vendors."
        with get_session() as session:
            try:
                return (session.query(Supplier)
                        .filter(Supplier.is_active == True)
                        .order_by(Supplier.name)
                        .limit(limit)
                        .all())
            except Exception as e:
                logger.error(f"Vendors query error: {e}")
                return []

    @classmethod
    def get_all_warehouses(cls, limit: int = 50) -> List[Warehouse]:
        "Get all warehouses."
        with get_session() as session:
            try:
                return (session.query(Warehouse)
                        .options(joinedload(Warehouse.manager))
                        .filter(Warehouse.is_active == True)
                        .order_by(Warehouse.name)
                        .limit(limit)
                        .all())
            except Exception as e:
                logger.error(f"Warehouses query error: {e}")
                return []

    @classmethod
    def get_all_assets(cls, limit: int = 50) -> List[Asset]:
        "Get all assets."
        with get_session() as session:
            try:
                return (session.query(Asset)
                        .options(joinedload(Asset.assigned_to),
                                 joinedload(Asset.warehouse))
                        .order_by(Asset.created_at.desc())
                        .limit(limit)
                        .all())
            except Exception as e:
                logger.error(f"Assets query error: {e}")
                return []

    @classmethod
    def get_all_contracts(cls, limit: int = 50) -> List[Contract]:
        "Get all contracts."
        with get_session() as session:
            try:
                return (session.query(Contract)
                        .order_by(Contract.created_at.desc())
                        .limit(limit)
                        .all())
            except Exception as e:
                logger.error(f"Contracts query error: {e}")
                return []

    @classmethod
    def get_all_invoices(cls, limit: int = 50) -> List[Invoice]:
        "Get all invoices."
        with get_session() as session:
            try:
                return (session.query(Invoice)
                        .order_by(Invoice.created_at.desc())
                        .limit(limit)
                        .all())
            except Exception as e:
                logger.error(f"Invoices query error: {e}")
                return []

    @classmethod
    def create_test_data(cls) -> Dict[str, int]:
        "Create test data for CRM (enhanced 15 events)."
        test_data = {}
        try:
            with get_session() as session:
                test_user = session.query(User).first()
                if not test_user:
                    logger.warning('No users for test data')
                    return {}

                # Leads
                for i in range(10):
                    lead = Lead(
                        name=f'Test Lead {i+1}',
                        company=f'ABC Corp {i+1}',
                        email=f'lead{i+1}@test.com',
                        phone=f'+91-900000000{i+1}',
                        value=10000 + i*1000,
                        source='website',
                        status='new',
                        assigned_to_id=test_user.id
                    )
                    session.add(lead)
                test_data['leads'] = 10

                # Contacts
                for i in range(10):
                    contact = Contact(
                        first_name='John',
                        last_name=f'Doe {i+1}',
                        company=f'Doe Enterprises {i+1}',
                        email=f'john.doe{i+1}@test.com',
                        phone=f'+91-911111111{i+1}',
                        is_customer=True
                    )
                    session.add(contact)
                test_data['contacts'] = 10

                # Events - 15 events across 2 weeks
                logger.info("📅 Creating 15 test events...")
                for i in range(15):
                    days_offset = i // 3
                    start_date = datetime.now().date() - timedelta(days=days_offset*2)
                    start = datetime.combine(
                        start_date, datetime.time(9 + (i % 3)*2, 0))
                    end = start + timedelta(hours=1, minutes=30)

                    title = f"Team Meeting {i+1}"
                    event = CalendarEvent(
                        title=title,
                        description=f"Test calendar event {i+1} for dialog visibility",
                        start_time=start,
                        end_time=end,
                        location=f"Room {chr(65 + i % 6)}",
                        organizer_id=test_user.id
                    )
                    session.add(event)
                test_data['events'] = 15

                # Vendors
                for i in range(3):
                    vendor = Supplier(
                        name=f'Test Vendor {i+1}',
                        email=f'vendor{i+1}@test.com',
                        phone=f'+91-900000000{i+1}',
                        is_active=True
                    )
                    session.add(vendor)
                test_data['vendors'] = 3

                session.commit()
                logger.info(f'✅ Enhanced test data: {test_data}')
        except Exception as e:
            logger.error(f"Test data error: {e}")
            test_data = {}
        return test_data


crm_repo = CRMRRepository()
