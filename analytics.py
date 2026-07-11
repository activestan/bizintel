"""
Analytics engine: computes KPIs and operational metrics.
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, date
from sqlalchemy import func, extract
from models import db, Transaction, Customer, Service, Resource, ResourceUsage, OperationalMetric


def get_summary_kpis():
    today = date.today()
    week_ago = today - timedelta(days=7)
    month_start = today.replace(day=1)

    today_tx = Transaction.query.filter(func.date(Transaction.created_at) == today).all()
    today_revenue = sum(t.total_amount for t in today_tx)
    today_count = len(today_tx)

    week_tx = Transaction.query.filter(func.date(Transaction.created_at) >= week_ago).all()
    week_revenue = sum(t.total_amount for t in week_tx)
    week_count = len(week_tx)

    month_tx = Transaction.query.filter(func.date(Transaction.created_at) >= month_start).all()
    month_revenue = sum(t.total_amount for t in month_tx)
    month_count = len(month_tx)

    month_customers = db.session.query(
        func.count(func.distinct(Transaction.customer_id))
    ).filter(func.date(Transaction.created_at) >= month_start).scalar() or 0

    avg_tx = month_revenue / month_count if month_count > 0 else 0.0

    total_resources = Resource.query.count()
    busy_resources = Resource.query.filter_by(status='in_use').count()
    utilization = (busy_resources / total_resources * 100) if total_resources > 0 else 0

    return {
        'today_revenue': round(today_revenue, 2),
        'today_transactions': today_count,
        'week_revenue': round(week_revenue, 2),
        'week_transactions': week_count,
        'month_revenue': round(month_revenue, 2),
        'month_transactions': month_count,
        'month_unique_customers': month_customers,
        'avg_transaction_value': round(avg_tx, 2),
        'resource_utilization': round(utilization, 1),
    }


def get_revenue_trend(days=30):
    start = date.today() - timedelta(days=days)
    results = db.session.query(
        func.date(Transaction.created_at).label('day'),
        func.sum(Transaction.total_amount).label('revenue'),
        func.count(Transaction.id).label('count')
    ).filter(func.date(Transaction.created_at) >= start).group_by(
        func.date(Transaction.created_at)
    ).order_by('day').all()

    return {
        'labels': [str(r.day) for r in results],
        'revenue': [round(float(r.revenue or 0), 2) for r in results],
        'transactions': [r.count for r in results],
    }


def get_service_breakdown(start_date=None, end_date=None):
    if start_date is None:
        start_date = date.today().replace(day=1)
    if end_date is None:
        end_date = date.today()

    results = db.session.query(
        Service.category,
        func.sum(Transaction.total_amount).label('revenue'),
        func.count(Transaction.id).label('count')
    ).join(Transaction, Transaction.service_id == Service.id).filter(
        func.date(Transaction.created_at) >= start_date,
        func.date(Transaction.created_at) <= end_date
    ).group_by(Service.category).order_by(func.sum(Transaction.total_amount).desc()).all()

    return {
        'labels': [r.category for r in results],
        'revenue': [round(float(r.revenue or 0), 2) for r in results],
        'counts': [r.count for r in results],
    }


def get_hourly_distribution(days=7):
    start = date.today() - timedelta(days=days)
    results = db.session.query(
        extract('hour', Transaction.created_at).label('hour'),
        func.count(Transaction.id).label('count'),
        func.sum(Transaction.total_amount).label('revenue')
    ).filter(func.date(Transaction.created_at) >= start).group_by('hour').order_by('hour').all()

    hours = list(range(24))
    counts = [0] * 24
    revenues = [0.0] * 24
    for r in results:
        if r.hour is not None:
            counts[int(r.hour)] = r.count
            revenues[int(r.hour)] = round(float(r.revenue or 0), 2)

    peak_hour = int(np.argmax(counts)) if any(counts) else None

    return {
        'labels': [f'{h:02d}:00' for h in hours],
        'counts': counts,
        'revenues': revenues,
        'peak_hour': peak_hour,
    }


def get_top_services(limit=5):
    month_start = date.today().replace(day=1)
    results = db.session.query(
        Service.name,
        func.sum(Transaction.total_amount).label('revenue'),
        func.count(Transaction.id).label('count')
    ).join(Transaction, Transaction.service_id == Service.id).filter(
        func.date(Transaction.created_at) >= month_start
    ).group_by(Service.name).order_by(func.sum(Transaction.total_amount).desc()).limit(limit).all()

    return [{'name': r.name, 'revenue': round(float(r.revenue or 0), 2), 'count': r.count} for r in results]


def get_customer_metrics():
    total_customers = Customer.query.count()
    repeat_customers = Customer.query.filter(Customer.total_visits > 1).count()
    retention_pct = (repeat_customers / total_customers * 100) if total_customers > 0 else 0
    top = Customer.query.order_by(Customer.total_spent.desc()).limit(10).all()

    return {
        'total_customers': total_customers,
        'repeat_customers': repeat_customers,
        'retention_pct': round(retention_pct, 1),
        'top_customers': [{'name': c.name, 'visits': c.total_visits, 'spent': round(c.total_spent, 2)} for c in top],
    }


def compute_daily_metrics(target_date=None):
    if target_date is None:
        target_date = date.today()

    day_tx = Transaction.query.filter(func.date(Transaction.created_at) == target_date).all()
    if not day_tx:
        return None

    total_rev = sum(t.total_amount for t in day_tx)
    tx_count = len(day_tx)
    unique_cust = len(set(t.customer_id for t in day_tx if t.customer_id))
    avg_tx = total_rev / tx_count if tx_count > 0 else 0

    hour_counts = {}
    for t in day_tx:
        h = t.created_at.hour
        hour_counts[h] = hour_counts.get(h, 0) + 1
    peak = max(hour_counts, key=hour_counts.get) if hour_counts else None

    total_res = Resource.query.count()
    usage_count = ResourceUsage.query.filter(func.date(ResourceUsage.start_time) == target_date).count()
    util_pct = (usage_count / (total_res * 8) * 100) if total_res > 0 else 0
    util_pct = min(util_pct, 100.0)

    svc_rev = {}
    for t in day_tx:
        svc_rev[t.service_id] = svc_rev.get(t.service_id, 0) + t.total_amount
    top_svc = max(svc_rev, key=svc_rev.get) if svc_rev else None

    existing = OperationalMetric.query.filter_by(date=target_date).first()
    if existing:
        existing.total_revenue = total_rev
        existing.total_transactions = tx_count
        existing.unique_customers = unique_cust
        existing.avg_transaction_value = round(avg_tx, 2)
        existing.peak_hour = peak
        existing.resource_utilization_pct = round(util_pct, 1)
        existing.top_service_id = top_svc
    else:
        metric = OperationalMetric(
            date=target_date, total_revenue=total_rev, total_transactions=tx_count,
            unique_customers=unique_cust, avg_transaction_value=round(avg_tx, 2),
            peak_hour=peak, resource_utilization_pct=round(util_pct, 1),
            top_service_id=top_svc,
        )
        db.session.add(metric)

    db.session.commit()
    return True
