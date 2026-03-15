#!/usr/bin/env python3
"""
Fix orphaned email_recipients causing Employee deletion crash
Run: python3 scripts/fix_email_recipients.py
"""
import sys
import os
from database.connection import get_engine, get_session
from database.models import EmailRecipient, EmailMessage, User
from sqlalchemy import text
import logging
import config_local
DATABASE_URL = config_local.DATABASE_URL
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def fix_orphaned_recipients():
    """Delete orphaned EmailRecipient records with invalid recipient_id"""
    with get_session() as session:
        # Find orphaned recipients (recipient_id doesn't exist in users)
        orphaned = session.query(EmailRecipient).outerjoin(User, EmailRecipient.recipient_id == User.id).filter(
            User.id.is_(None)
        ).all()

        logger.info(f"Found {len(orphaned)} orphaned EmailRecipient records")

        if orphaned:
            for rec in orphaned:
                logger.info(
                    f"Deleting orphaned EmailRecipient ID {rec.id} (recipient_id={rec.recipient_id})")
                session.delete(rec)

            session.commit()
            logger.info("✅ Orphaned EmailRecipient records cleaned")
        else:
            logger.info("✅ No orphaned records found")


def check_employee_1_data():
    """Check Employee 1 and related data status"""
    with get_session() as session:
        # Check if Employee 1 exists
        emp1 = session.query(EmailMessage).filter(
            EmailMessage.sender_id == 1
        ).count()

        logger.info(f"EmailMessages with sender_id=1: {emp1}")

        rec_count = session.query(EmailRecipient).filter(
            EmailRecipient.recipient_id == 1
        ).count()
        logger.info(f"EmailRecipients with recipient_id=1: {rec_count}")


def main():
    if not DATABASE_URL:
        logger.error("❌ DATABASE_URL not set")
        return 1

    logger.info("🔧 Fixing email_recipients data integrity issues...")
    fix_orphaned_recipients()
    logger.info("\n📊 Employee 1 Data Check:")
    check_employee_1_data()
    logger.info("✅ Data cleanup completed!")
    return 0


if __name__ == "__main__":
    exit(main())
