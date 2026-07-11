"""
Decision support engine: detects operational inefficiencies and logs recommendations.
"""
from datetime import date, timedelta
from sqlalchemy import func
from models import db, Transaction, Resource, Service, Customer, EfficiencyInsight


def generate_insights():
    insights = []
    result = _check_peak_hour()
    if result: insights.append(result)
    result = _check_underperforming_services()
    if result: insights.append(result)
    result = _check_resource_utilization()
    if result: insights.append(result)
    result = _check_customer_retention()
    if result: insights.append(result)
    result = _check_slow_days()
    if result: insights.append(result)
    result = _check_high_value_opportunities()
    if result: insights.append(result)
    db.session.commit()
    return insights


def _check_peak_hour():
    week_ago = date.today() - timedelta(days=14)
    result = db.session.query(
        func.extract('hour', Transaction.created_at).label('hour'),
        func.count(Transaction.id).label('count')
    ).filter(func.date(Transaction.created_at) >= week_ago).group_by('hour').order_by(
        func.count(Transaction.id).desc()).first()

    if not result:
        return None

    peak_hour = int(result.hour) if result.hour is not None else 12
    peak_count = result.count

    existing = EfficiencyInsight.query.filter_by(
        category='recommendation', metric_name='peak_hour'
    ).filter(EfficiencyInsight.created_at >= date.today()).first()

    if not existing:
        insight = EfficiencyInsight(
            category='recommendation',
            title='Peak Hour Staffing: {:02d}:00 - {:02d}:00'.format(peak_hour, peak_hour + 1),
            description='The busiest hour is {:02d}:00 to {:02d}:00 with an average of {} transactions. Schedule more staff during this window to reduce wait times.'.format(peak_hour, peak_hour + 1, peak_count),
            severity='info', metric_name='peak_hour', metric_value=float(peak_hour),
        )
        db.session.add(insight)
        return insight
    return None


def _check_underperforming_services():
    month_start = date.today().replace(day=1)
    svc_results = db.session.query(
        Service.name, func.count(Transaction.id).label('tx_count')
    ).outerjoin(Transaction, Transaction.service_id == Service.id).filter(
        func.date(Transaction.created_at) >= month_start
    ).group_by(Service.name).having(func.count(Transaction.id) <= 2).all()

    if svc_results:
        names = [s.name for s in svc_results]
        existing = EfficiencyInsight.query.filter_by(
            category='alert', metric_name='low_demand_services'
        ).filter(EfficiencyInsight.created_at >= month_start).first()

        if not existing:
            insight = EfficiencyInsight(
                category='alert', title='Low-Demand Services Found',
                description='These services had 2 or fewer transactions this month: {}. Consider promotions or bundling.'.format(', '.join(names)),
                severity='warning', metric_name='low_demand_services', metric_value=len(names),
            )
            db.session.add(insight)
            return insight
    return None


def _check_resource_utilization():
    total = Resource.query.count()
    if total == 0:
        return None
    in_use = Resource.query.filter_by(status='in_use').count()
    util_pct = (in_use / total * 100)

    if util_pct > 80:
        existing = EfficiencyInsight.query.filter_by(
            category='bottleneck', metric_name='high_resource_utilization'
        ).filter(EfficiencyInsight.created_at >= date.today()).first()
        if not existing:
            insight = EfficiencyInsight(
                category='bottleneck', title='High Resource Utilisation',
                description='Resources at {}% utilisation. Consider adding more workstations to meet demand.'.format(round(util_pct)),
                severity='critical', metric_name='high_resource_utilization', metric_value=round(util_pct, 1),
            )
            db.session.add(insight)
            return insight
    elif util_pct < 30:
        existing = EfficiencyInsight.query.filter_by(
            category='opportunity', metric_name='low_resource_utilization'
        ).filter(EfficiencyInsight.created_at >= date.today()).first()
        if not existing:
            insight = EfficiencyInsight(
                category='opportunity', title='Low Resource Utilisation',
                description='Resources only at {}% utilisation. Introduce new services or run a promotion to attract more customers.'.format(round(util_pct)),
                severity='info', metric_name='low_resource_utilization', metric_value=round(util_pct, 1),
            )
            db.session.add(insight)
            return insight
    return None


def _check_customer_retention():
    total = Customer.query.count()
    if total == 0:
        return None
    repeat = Customer.query.filter(Customer.total_visits > 1).count()
    retention = (repeat / total * 100)

    if retention < 40:
        existing = EfficiencyInsight.query.filter_by(
            category='recommendation', metric_name='customer_retention'
        ).filter(EfficiencyInsight.created_at >= date.today()).first()
        if not existing:
            insight = EfficiencyInsight(
                category='recommendation', title='Low Customer Retention ({}%)'.format(round(retention)),
                description='Only {}% of customers return. Start a loyalty programme to improve repeat business.'.format(round(retention)),
                severity='warning', metric_name='customer_retention', metric_value=round(retention, 1),
            )
            db.session.add(insight)
            return insight
    return None


def _check_slow_days():
    days_ago = date.today() - timedelta(days=30)
    daily = db.session.query(
        func.date(Transaction.created_at).label('day'),
        func.count(Transaction.id).label('count')
    ).filter(func.date(Transaction.created_at) >= days_ago).group_by('day').all()

    if len(daily) < 5:
        return None
    counts = [d.count for d in daily]
    avg = sum(counts) / len(counts)
    threshold = avg * 0.5
    slow_days = [str(d.day) for d in daily if d.count < threshold]

    if slow_days and len(slow_days) >= 3:
        existing = EfficiencyInsight.query.filter_by(
            category='alert', metric_name='slow_days'
        ).filter(EfficiencyInsight.created_at >= date.today()).first()
        if not existing:
            insight = EfficiencyInsight(
                category='alert', title='Consistently Low-Traffic Days',
                description='Days under 50% of average volume: {}. Target these days with promotions or adjust hours.'.format(', '.join(slow_days[:5])),
                severity='warning', metric_name='slow_days', metric_value=len(slow_days),
            )
            db.session.add(insight)
            return insight
    return None


def _check_high_value_opportunities():
    month_start = date.today().replace(day=1)
    svc_data = db.session.query(
        Service.name, Service.unit_price, func.count(Transaction.id).label('count')
    ).outerjoin(Transaction, Transaction.service_id == Service.id).filter(
        func.date(Transaction.created_at) >= month_start
    ).group_by(Service.name, Service.unit_price).all()

    high_value = [(s.name, s.unit_price) for s in svc_data if s.unit_price and s.unit_price > 500 and s.count < 5]
    if high_value:
        existing = EfficiencyInsight.query.filter_by(
            category='opportunity', metric_name='high_value_services'
        ).filter(EfficiencyInsight.created_at >= date.today()).first()
        if not existing:
            names = [n for n, _ in high_value]
            insight = EfficiencyInsight(
                category='opportunity', title='Promote High-Value Services',
                description='High-value services with low volumes: {}. Boost visibility through upselling.'.format(', '.join(names)),
                severity='success', metric_name='high_value_services', metric_value=len(high_value),
            )
            db.session.add(insight)
            return insight
    return None


def get_all_insights(limit=20):
    return EfficiencyInsight.query.order_by(EfficiencyInsight.created_at.desc()).limit(limit).all()


def get_unread_count():
    return EfficiencyInsight.query.filter_by(is_read=False).count()


def mark_read(insight_id):
    insight = EfficiencyInsight.query.get(insight_id)
    if insight:
        insight.is_read = True
        db.session.commit()
