"""
Predictive engine: demand and resource utilisation forecasting using regression.
"""
import numpy as np
import pandas as pd
from datetime import date, timedelta
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from sqlalchemy import func
from models import db, Transaction, OperationalMetric, ForecastResult


def _get_historical_data(days=90):
    start = date.today() - timedelta(days=days)
    results = db.session.query(
        func.date(Transaction.created_at).label('day'),
        func.sum(Transaction.total_amount).label('revenue'),
        func.count(Transaction.id).label('count')
    ).filter(func.date(Transaction.created_at) >= start).group_by('day').order_by('day').all()
    return [(r.day, float(r.revenue or 0), r.count) for r in results]


def _get_metrics_data(days=90):
    start = date.today() - timedelta(days=days)
    metrics = OperationalMetric.query.filter(
        OperationalMetric.date >= start
    ).order_by(OperationalMetric.date).all()
    return [(m.date, m.total_transactions, m.total_revenue, m.resource_utilization_pct) for m in metrics]


def forecast_demand(days_ahead=7):
    historical = _get_historical_data(90)
    if len(historical) < 7:
        return {'error': 'Need at least 7 days of data', 'forecasts': []}

    df = pd.DataFrame(historical, columns=['day', 'revenue', 'count'])
    X = np.arange(len(df)).reshape(-1, 1)
    y_counts = df['count'].values
    y_revenue = df['revenue'].values

    poly = PolynomialFeatures(degree=2, include_bias=False)
    X_poly = poly.fit_transform(X)

    model_counts = LinearRegression().fit(X_poly, y_counts)
    model_revenue = LinearRegression().fit(X_poly, y_revenue)

    r2_counts = model_counts.score(X_poly, y_counts)
    r2_revenue = model_revenue.score(X_poly, y_revenue)

    future_X = np.arange(len(df), len(df) + days_ahead).reshape(-1, 1)
    future_X_poly = poly.transform(future_X)

    predicted_counts = model_counts.predict(future_X_poly)
    predicted_revenue = model_revenue.predict(future_X_poly)

    residuals_counts = y_counts - model_counts.predict(X_poly)
    std_counts = np.std(residuals_counts)
    residuals_rev = y_revenue - model_revenue.predict(X_poly)
    std_rev = np.std(residuals_rev)

    forecasts = []
    for i in range(days_ahead):
        f_date = date.today() + timedelta(days=i + 1)
        c = max(0, predicted_counts[i])
        r = max(0, predicted_revenue[i])
        forecasts.append({
            'date': str(f_date), 'day_name': f_date.strftime('%A'),
            'predicted_transactions': round(c), 'predicted_revenue': round(r, 2),
            'count_lower': max(0, round(c - 1.96 * std_counts)),
            'count_upper': round(c + 1.96 * std_counts),
            'revenue_lower': max(0, round(r - 1.96 * std_rev, 2)),
            'revenue_upper': round(r + 1.96 * std_rev, 2),
        })

    for fc in forecasts:
        existing = ForecastResult.query.filter_by(
            forecast_type='demand', forecast_date=date.fromisoformat(fc['date'])
        ).first()
        if existing:
            existing.predicted_value = fc['predicted_transactions']
            existing.confidence_lower = fc['count_lower']
            existing.confidence_upper = fc['count_upper']
        else:
            fr = ForecastResult(
                forecast_type='demand', forecast_date=date.fromisoformat(fc['date']),
                predicted_value=fc['predicted_transactions'],
                confidence_lower=fc['count_lower'], confidence_upper=fc['count_upper'],
                model_used='PolynomialRegression',
            )
            db.session.add(fr)
    db.session.commit()

    return {
        'model_accuracy': round(r2_counts * 100, 1),
        'revenue_model_accuracy': round(r2_revenue * 100, 1),
        'forecasts': forecasts,
    }


def forecast_resource_utilization(days_ahead=7):
    metrics = _get_metrics_data(90)
    if len(metrics) < 7:
        return {'error': 'Need at least 7 days of metrics data', 'forecasts': []}

    df = pd.DataFrame(metrics, columns=['date', 'transactions', 'revenue', 'utilization'])
    df = df.dropna(subset=['utilization'])
    if len(df) < 5:
        return {'error': 'Not enough utilisation data', 'forecasts': []}

    X = np.arange(len(df)).reshape(-1, 1)
    y = df['utilization'].values

    model = LinearRegression().fit(X, y)
    r2 = model.score(X, y)
    residuals = y - model.predict(X)
    std = np.std(residuals)

    predictions = model.predict(np.arange(len(df), len(df) + days_ahead).reshape(-1, 1))

    forecasts = []
    for i in range(days_ahead):
        f_date = date.today() + timedelta(days=i + 1)
        val = max(0, min(100, predictions[i]))
        forecasts.append({
            'date': str(f_date), 'day_name': f_date.strftime('%A'),
            'predicted_utilization': round(val, 1),
            'lower': max(0, round(val - 1.96 * std, 1)),
            'upper': min(100, round(val + 1.96 * std, 1)),
        })

    return {'model_accuracy': round(r2 * 100, 1), 'forecasts': forecasts}


def analyze_trends():
    historical = _get_historical_data(90)
    if len(historical) < 14:
        return {'trend': 'insufficient_data', 'summary': 'Need at least 14 days of data.'}

    df = pd.DataFrame(historical, columns=['day', 'revenue', 'count'])
    df['day_idx'] = range(len(df))

    X = df['day_idx'].values.reshape(-1, 1)
    y = df['revenue'].values
    model = LinearRegression().fit(X, y)
    slope = model.coef_[0]

    if slope > 1.0:
        trend_type = 'growth'
        trend_pct = abs(slope) / (y.mean() or 1) * 100
    elif slope < -1.0:
        trend_type = 'decline'
        trend_pct = abs(slope) / (y.mean() or 1) * 100
    else:
        trend_type = 'stable'
        trend_pct = 0

    df['dow'] = pd.to_datetime(df['day']).dt.dayofweek
    dow_avg = df.groupby('dow')['revenue'].mean()
    day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    best_day = int(dow_avg.idxmax())
    worst_day = int(dow_avg.idxmin())

    return {
        'trend': trend_type, 'trend_pct': round(trend_pct, 1),
        'avg_daily_revenue': round(float(y.mean()), 2),
        'avg_daily_transactions': round(float(df['count'].mean()), 1),
        'best_day': day_names[best_day], 'worst_day': day_names[worst_day],
        'best_day_avg_revenue': round(float(dow_avg.iloc[best_day]), 2),
        'worst_day_avg_revenue': round(float(dow_avg.iloc[worst_day]), 2),
        'total_period_revenue': round(float(y.sum()), 2),
        'total_period_transactions': int(df['count'].sum()),
    }
