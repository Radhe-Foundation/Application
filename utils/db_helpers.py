"""
Database Helper Utilities
Provides simple and safe database operations
"""

from database.session_manager import get_session


def quick_query(model, **filters):
    """Quick query helper for simple operations."""
    with get_session() as session:
        query = session.query(model)
        for key, value in filters.items():
            if hasattr(model, key):
                query = query.filter(getattr(model, key) == value)

        if 'id' in filters:
            return query.first()
        return query.all()


def quick_count(model, **filters):
    """Quick count helper."""
    with get_session() as session:
        query = session.query(model)
        for key, value in filters.items():
            if hasattr(model, key):
                query = query.filter(getattr(model, key) == value)
        return query.count()


def quick_create(model, **kwargs):
    """Quick create helper."""
    with get_session() as session:
        instance = model(**kwargs)
        session.add(instance)
        session.commit()
        session.refresh(instance)
        return instance


def quick_update(model, id, **kwargs):
    """Quick update helper."""
    with get_session() as session:
        instance = session.query(model).get(id)
        if instance:
            for key, value in kwargs.items():
                if hasattr(instance, key):
                    setattr(instance, key, value)
            session.commit()
            session.refresh(instance)
        return instance


def quick_delete(model, id) -> bool:
    """Quick delete helper."""
    with get_session() as session:
        instance = session.query(model).get(id)
        if instance:
            session.delete(instance)
            session.commit()
            return True
        return False
