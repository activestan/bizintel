"""
Decision support engine: detects operational inefficiencies and logs recommendations.
Each rule generates one insight per period. Duplicate checks prevent spam.
"""
from datetime import date, timedelta
from sqlalchemy import func
from models import db, Transaction, Resource, Service, Customer, EfficiencyInsight


def generate_insights():
    """
    Run all 6 diagnostic checks. Each check only fires once per period
    (today for daily checks, this month for monthly checks) to avoid
    repeat alerts for the same issue.
    """
    insights = []
    for checker in [
        _check_peak_hour_staffing,
        _check_underperforming_services,
        _check_resource_balance,
        _check_customer_retention,
        _check_slow_days,
        _check_high_value_gaps,
    ]:
        result = checker()
        if result:
            insights.append(result)
    db.session.commit()
    return insights


def insight_frequency_info():
    """Returns explanation of how often each insight type refreshes."""
    return [
        ('Peak Hour Staffing', 'Daily', 'Checks the last 14 days of transactions. Updates if peak hour shifts.'),
        ('Underperforming Services', 'Monthly', 'Compares current month transactions. Resets at the start of each month.'),
        ('Resource Balance', 'Daily', 'Checks current resource status. Changes as workstations are occupied or freed.'),
        ('Customer Retention', 'Daily', 'Calculated from all customer records. Updates as new customers are added.'),
        ('Slow-Traffic Days', 'Daily', 'Analyzes the last 30 days. The list of slow days shifts as new data comes in.'),
        ('High-Value Service Gaps', 'Daily', 'Finds services with high price but low monthly volume. Refreshes with each new transaction.'),
    ]


def _check_peak_hour_staffing():
    """
    Finds the busiest hour and suggests scheduling more staff then.
    Checks once per day to avoid repeat alerts.
    """
    two_weeks_ago = date.today() - timedelta(days=14)
    result = db.session.query(
        func.extract('hour', Transaction.created_at).label('hour'),
        func.count(Transaction.id).label('count')
    ).filter(
        func.date(Transaction.created_at) >= two_weeks_ago
    ).group_by('hour').order_by(func.count(Transaction.id).desc()).first()

    if not result:
        return None

    peak_hour = int(result.hour) if result.hour is not None else 12
    peak_count = result.count

    # Only fire once today
    existing = EfficiencyInsight.query.filter_by(
        category='recommendation', metric_name='peak_hour'
    ).filter(EfficiencyInsight.created_at >= date.today()).first()

    if not existing:
        periods = ['morning', 'midday', 'afternoon']
        period_name = periods[0] if peak_hour < 11 else (periods[1] if peak_hour < 15 else periods[2])
        insight = EfficiencyInsight(
            category='recommendation',
            title='Schedule More Staff From {:02d}:00 to {:02d}:00'.format(peak_hour, peak_hour + 1),
            description=(
                'Your busiest period is the {} hour between {:02d}:00 and {:02d}:00. '
                'About {} customers are served during this window each day. '
                'Having at least 2 staff members on duty at this time will reduce '
                'customer waiting and prevent billing mistakes during the rush.'
            ).format(period_name, peak_hour, peak_hour + 1, round(peak_count / 14)),
            severity='info',
            metric_name='peak_hour',
            metric_value=float(peak_hour),
        )
        db.session.add(insight)
        return insight
    return None


def _check_underperforming_services():
    """
    Flags services with very few or zero transactions this month.
    Checks once per month.
    """
    month_start = date.today().replace(day=1)
    svc_results = db.session.query(
        Service.name, Service.category, func.count(Transaction.id).label('tx_count')
    ).outerjoin(Transaction, Transaction.service_id == Service.id).filter(
        func.date(Transaction.created_at) >= month_start
    ).group_by(Service.name, Service.category).having(
        func.count(Transaction.id) <= 2
    ).all()

    if svc_results:
        existing = EfficiencyInsight.query.filter_by(
            category='alert', metric_name='low_demand_services'
        ).filter(EfficiencyInsight.created_at >= month_start).first()

        if not existing:
            names = ['{} ({})'.format(s.name, s.category) for s in svc_results]
            insight = EfficiencyInsight(
                category='alert',
                title='{} Services Have Low Demand This Month'.format(len(svc_results)),
                description=(
                    'These services recorded 2 or fewer transactions since the start of this month: '
                    '{}. This may mean customers do not know about them or the pricing needs review. '
                    'Try placing a notice board listing these services, or offer a discount bundle '
                    '(e.g., \"Type and Print together at 10% off\") to increase uptake.'
                ).format(', '.join(names)),
                severity='warning',
                metric_name='low_demand_services',
                metric_value=len(names),
            )
            db.session.add(insight)
            return insight
    return None


def _check_resource_balance():
    """
    Checks if workstations are overused (bottleneck) or underused (idle).
    Checks once per day.
    """
    total = Resource.query.count()
    if total == 0:
        return None
    in_use = Resource.query.filter_by(status='in_use').count()
    util_pct = (in_use / total * 100)

    existing_high = EfficiencyInsight.query.filter_by(
        category='bottleneck', metric_name='high_resource_utilization'
    ).filter(EfficiencyInsight.created_at >= date.today()).first()

    existing_low = EfficiencyInsight.query.filter_by(
        category='opportunity', metric_name='low_resource_utilization'
    ).filter(EfficiencyInsight.created_at >= date.today()).first()

    if util_pct > 75 and not existing_high:
        insight = EfficiencyInsight(
            category='bottleneck',
            title='Workstations Nearly Full ({}% in Use)'.format(round(util_pct)),
            description=(
                '{} out of {} workstations are currently occupied. Customers may be waiting '
                'for a free computer during peak times. If this happens regularly, consider '
                'adding 2-3 more desktop PCs or converting some single sessions into 30-minute '
                'slots to serve more people per day.'
            ).format(in_use, total),
            severity='critical',
            metric_name='high_resource_utilization',
            metric_value=round(util_pct, 1),
        )
        db.session.add(insight)
        return insight

    if util_pct < 20 and not existing_low:
        insight = EfficiencyInsight(
            category='opportunity',
            title='Most Workstations Are Idle ({}% in Use)'.format(round(util_pct)),
            description=(
                'Only {} out of {} workstations are currently active. These idle computers '
                'still consume power and occupy space. Consider running a \"Happy Hour\" discount '
                'on internet browsing during these slow periods, or advertising your training '
                'classes to fill the empty seats productively.'
            ).format(in_use, total),
            severity='info',
            metric_name='low_resource_utilization',
            metric_value=round(util_pct, 1),
        )
        db.session.add(insight)
        return insight
    return None


def _check_customer_retention():
    """
    Checks what percentage of customers return more than once.
    Generates once per day if retention is low.
    """
    total = Customer.query.count()
    if total == 0:
        return None
    repeat = Customer.query.filter(Customer.total_visits > 1).count()
    retention = (repeat / total * 100)

    if retention < 50:
        existing = EfficiencyInsight.query.filter_by(
            category='recommendation', metric_name='customer_retention'
        ).filter(EfficiencyInsight.created_at >= date.today()).first()
        if not existing:
            insight = EfficiencyInsight(
                category='recommendation',
                title='Only {}% of Customers Return ({} out of {})'.format(
                    round(retention), repeat, total),
                description=(
                    '{} of your {} registered customers have visited more than once. '
                    'A simple loyalty system can improve this. Try giving every customer '
                    'a small card: after 5 visits, the 6th internet session is free. '
                    'Also, always ask new customers for their name and phone number so you '
                    'can send them a reminder about your services.'
                ).format(repeat, total),
                severity='warning',
                metric_name='customer_retention',
                metric_value=round(retention, 1),
            )
            db.session.add(insight)
            return insight
    return None


def _check_slow_days():
    """
    Finds days of the week that consistently underperform.
    Checks once per day based on the last 30 days.
    """
    thirty_days_ago = date.today() - timedelta(days=30)
    daily = db.session.query(
        func.date(Transaction.created_at).label('day'),
        func.count(Transaction.id).label('count')
    ).filter(func.date(Transaction.created_at) >= thirty_days_ago).group_by('day').all()

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
                category='alert',
                title='{} Very Slow Days Detected in the Last Month'.format(len(slow_days)),
                description=(
                    'The following dates had fewer than half the usual customer traffic: {}. '
                    'If you notice a pattern (e.g. certain weekdays are always slow), try '
                    'opening later or closing earlier on those days to reduce running costs. '
                    'You could also use slow days for equipment maintenance or staff training '
                    'instead of staying fully open with few customers.'
                ).format(', '.join(slow_days[:5])),
                severity='warning',
                metric_name='slow_days',
                metric_value=len(slow_days),
            )
            db.session.add(insight)
            return insight
    return None


def _check_high_value_gaps():
    """
    Finds high-unit-price services that have very few transactions,
    representing untapped revenue opportunities.
    Checks once per day.
    """
    month_start = date.today().replace(day=1)
    svc_data = db.session.query(
        Service.name, Service.unit_price, func.count(Transaction.id).label('count')
    ).outerjoin(Transaction, Transaction.service_id == Service.id).filter(
        func.date(Transaction.created_at) >= month_start
    ).group_by(Service.name, Service.unit_price).all()

    high_value = [(s.name, s.unit_price) for s in svc_data 
                  if s.unit_price and s.unit_price > 1500 and s.count < 3]
    if high_value:
        existing = EfficiencyInsight.query.filter_by(
            category='opportunity', metric_name='high_value_services'
        ).filter(EfficiencyInsight.created_at >= date.today()).first()
        if not existing:
            names = [n for n, _ in high_value[:5]]
            insight = EfficiencyInsight(
                category='opportunity',
                title='{} High-Value Services Are Not Selling Enough'.format(len(high_value)),
                description=(
                    'Services like {} generate good revenue per transaction but have very '
                    'few customers this month. Since each sale of these services brings in '
                    'more than a typical printing or browsing session, even 2-3 extra customers '
                    'would make a noticeable difference to your monthly total. Ask customers who '
                    'come for typing or printing if they also need these services.'
                ).format(', '.join(names)),
                severity='success',
                metric_name='high_value_services',
                metric_value=len(high_value),
            )
            db.session.add(insight)
            return insight
    return None


def get_all_insights(limit=20):
    return EfficiencyInsight.query.order_by(
        EfficiencyInsight.created_at.desc()
    ).limit(limit).all()


def get_unread_count():
    return EfficiencyInsight.query.filter_by(is_read=False).count()


def mark_read(insight_id):
    insight = EfficiencyInsight.query.get(insight_id)
    if insight:
        insight.is_read = True
        db.session.commit()
