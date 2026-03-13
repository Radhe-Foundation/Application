#!/usr/bin/env python3
\"\"\"CRM Test Data Generator - Populates all CRM tables with realistic data\"\"\"

import sys
import logging
from datetime import datetime, date, timedelta
sys.path.append('.')

from database.session_manager import get_session
from database.repositories import crm_repo
from database.models import User, Lead, Contact, CalendarEvent, Supplier, Warehouse, Asset, Contract, Invoice

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_crm_test_data():
    \"\"\"Generate comprehensive test data for ALL CRM modules.\"\"\"
    print("🚀 Generating CRM Test Data...")
    
    with get_session() as session:
        # Get test user
        user = session.query(User).first()
        if not user:
            print("❌ No users found. Create admin first.")
            return
        
        print(f"✅ Using user: {user.username}")
        
        created = {}
        
        # 1. LEADS (15)
        print("📊 Creating Leads...")
        leads = []
        for i in range(15):
            lead = Lead(
                name=f"Prospect {i+1} - Tech Innovators",
                company=f"TechCo {i+1}",
                email=f"prospect{i+1}@techco.com",
                phone=f"+91-98{i+1}00{i+1}00{i+1}",
                position="Decision Maker",
                source=['website','referral','cold_call'][i%3],
                status=['new','qualified','proposal','won'][i%4],
                value=50000 + i*2500,
                notes=f"High potential lead {i+1}",
                assigned_to_id=user.id
            )
            leads.append(lead)
        session.add_all(leads)
        created['leads'] = 15
        
        # 2. CONTACTS (12)
        print("👥 Creating Contacts...")
        contacts = []
        for i in range(12):
            contact = Contact(
                first_name=['John','Jane','Raj','Priya','Mike'][i%5],
                last_name=f"Doe{i+1}",
                company=f"ClientCorp {i+1}",
                email=f"contact{i+1}@clientcorp.com",
                phone=f"+91-99{i+1}11{i+1}11{i+1}",
                position=['CEO','Manager','Director'][i%3],
                is_customer=i%2==0
            )
            contacts.append(contact)
        session.add_all(contacts)
        created['contacts'] = 12
        
        # 3. EVENTS (8) 
        print("📅 Creating Events...")
        events = []
        for i in range(8):
            start = datetime.now() - timedelta(days=i*2)
            end = start + timedelta(hours=1, minutes=30)
            lead_id = leads[i%15].id if i < 15 else None
            contact_id = contacts[i%12].id if i < 12 else None
            
            event = CalendarEvent(
                title=f"Client Meeting {i+1}",
                description=f"Follow-up discussion with {['lead','contact'][i%2]}",
                start_time=start,
                end_time=end,
                location=f"Conference Room {chr(65+i%6)}",
                organizer_id=user.id,
                lead_id=lead_id,
                contact_id=contact_id,
                agenda=f"• Review progress\\n• Next steps"
            )
            events.append(event)
        session.add_all(events)
        created['events'] = 8
        
        # 4. VENDORS (5)
        print("🏪 Creating Vendors...")
        vendors = [
            Supplier(name="Global Tech Suppliers", contact_person="Raj Patel", email="raj@globaltech.com", phone="+91-9812345671", gst_number="27ABCDE1234F1Z5"),
            Supplier(name="Office Solutions Pvt Ltd", contact_person="Priya Sharma", email="priya@offsol.com", phone="+91-9823456782", gst_number="12FGHI5678J2K6"),
            Supplier(name="Digital Systems Inc", contact_person="Mike Johnson", email="mike@digitalsys.com", phone="+91-9834567893", gst_number="33JKLM9012N3O7"),
            Supplier(name="Pro Services", contact_person="Anita Desai", email="anita@proservices.in", phone="+91-9845678904", gst_number="45NOPQ3456R4S8"),
            Supplier(name="Elite Hardware", contact_person="Vikram Singh", email="vikram@elitehw.com", phone="+91-9856789015", gst_number="56QRST7890T5U9"),
        ]
        session.add_all(vendors)
        created['vendors'] = 5
        
        # 5. WAREHOUSES (3)
        print("🏭 Creating Warehouses...")
        warehouses = [
            Warehouse(name="Main Warehouse Mumbai", code="WH-MUM", city="Mumbai", state="Maharashtra", capacity=5000),
            Warehouse(name="Branch Delhi", code="WH-DEL", city="Delhi", state="Delhi", capacity=2000),
            Warehouse(name="Backup Facility", code="WH-BKP", city="Pune", state="Maharashtra", capacity=1000),
        ]
        session.add_all(warehouses)
        created['warehouses'] = 3
        
        # 6. ASSETS (10)
        print("💻 Creating Assets...")
        assets = []
        for i in range(10):
            assets.append(Asset(
                name=f"Laptop {chr(65+i)}-{i+1}",
                asset_code=f"LP{i+1:03d}",
                category=['electronics','other'][i%2],
                purchase_price=65000 + i*1000,
                current_value=55000 + i*800,
                status=['available','in_use'][i%2],
                serial_number=f"LN{i+1:08d}"
            ))
        session.add_all(assets)
        created['assets'] = 10
        
        # 7. CONTRACTS (6)
        print("📄 Creating Contracts...")
        contracts = []
        for i in range(6):
            contracts.append(Contract(
                title=f"Service Agreement {i+1}",
                contract_number=f"SA{i+1:04d}/2024",
                contract_type=['vendor','client'][i%2],
                value=250000 + i*50000,
                start_date=date.today(),
                end_date=date.today() + timedelta(days=365),
                status=['active','draft'][i%2],
                description=f"Annual service contract {i+1}"
            ))
        session.add_all(contracts)
        created['contracts'] = 6
        
        # 8. INVOICES (8)
        print("💰 Creating Invoices...")
        invoices = []
        for i in range(8):
            invoices.append(Invoice(
                invoice_number=f"INV{i+1:04d}/2024",
                customer_name=f"Client {chr(65+i%6)} Ltd",
                invoice_date=date.today() - timedelta(days=i),
                due_date=date.today() + timedelta(days=30),
                total_amount=12500 + i*2500,
                status=['draft','sent','paid'][i%3]
            ))
        session.add_all(invoices)
        created['invoices'] = 8
        
        session.commit()
        
        print("✅ CRM Test Data Generated Successfully!")
        print("📋 SUMMARY:")
        for k,v in created.items():
            print(f"   {k.upper()}: {v}")
        print("\n🔄 Refresh CRM screen to see data!")
        print("🎯 Test: Add/Edit/Delete → buttons now responsive!")
        
        return created

if __name__ == "__main__":
    generate_crm_test_data()

