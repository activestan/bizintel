"""
Intelligent Business Analytics System for Optimising Operations
in a Computing Business Hub.

Flask application entry point.
"""
import os
from datetime import date, datetime, timedelta
from flask import Flask, render_template, jsonify, request, redirect, url_for

from models import db, Service, Resource, Customer, Transaction, ResourceUsage, ForecastResult, EfficiencyInsight
from analytics import get_summary_kpis, get_revenue_trend, get_service_breakdown, get_hourly_distribution, get_top_services, get_customer_metrics, compute_daily_metrics
from predictive import forecast_demand, forecast_resource_utilization, analyze_trends
from decision_support import generate_insights, get_all_insights, get_unread_count, mark_read
from seed_data import seed_all


def create_app():
    app = Flask(__name__)
    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config['SECRET_KEY'] = 'biz-analytics-key-2026'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'analytics.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    with app.app_context():
        db.create_all()

    return app


app = create_app()


@app.context_processor
def inject_context():
    unread = 0
    try:
        unread = get_unread_count()
    except Exception:
        pass
    return dict(now=date.today(), unread_insights=unread)


# ---------- ROUTES ----------

@app.route('/')
def dashboard():
    try:
        kpis = get_summary_kpis()
        trend = get_revenue_trend(30)
        service_breakdown = get_service_breakdown()
        hourly = get_hourly_distribution(7)
        top_services = get_top_services(5)
        trend_analysis = analyze_trends()
        insights = get_all_insights(6)
        return render_template('dashboard.html', kpis=kpis, trend=trend,
                               service_breakdown=service_breakdown, hourly=hourly,
                               top_services=top_services, trend_analysis=trend_analysis,
                               insights=insights)
    except Exception as e:
        return render_template('dashboard.html', error=str(e))


@app.route('/analytics')
def analytics_page():
    try:
        trend = get_revenue_trend(60)
        service_bd = get_service_breakdown()
        hourly = get_hourly_distribution(30)
        customer_metrics = get_customer_metrics()
        return render_template('analytics.html', trend=trend,
                               service_breakdown=service_bd, hourly=hourly,
                               customer_metrics=customer_metrics)
    except Exception as e:
        return render_template('analytics.html', error=str(e))


@app.route('/predictions')
def predictions_page():
    try:
        demand = forecast_demand(14)
        resource_fc = forecast_resource_utilization(14)
        trends = analyze_trends()
        return render_template('predictions.html', demand=demand,
                               resource_forecast=resource_fc, trends=trends)
    except Exception as e:
        return render_template('predictions.html', error=str(e))


@app.route('/insights')
def insights_page():
    try:
        generate_insights()
        insights = get_all_insights(50)
        return render_template('insights.html', insights=insights)
    except Exception as e:
        return render_template('insights.html', error=str(e))


@app.route('/data-entry')
def data_entry_page():
    try:
        services = Service.query.filter_by(is_active=True).all()
        customers = Customer.query.order_by(Customer.name).all()
        resources = Resource.query.all()
        recent = Transaction.query.order_by(Transaction.created_at.desc()).limit(20).all()
        return render_template('data_entry.html', services=services,
                               customers=customers, resources=resources,
                               recent_transactions=recent)
    except Exception as e:
        return render_template('data_entry.html', error=str(e))


# ---------- API ----------

@app.route('/api/transaction', methods=['POST'])
def add_transaction():
    try:
        service_id = int(request.form.get('service_id'))
        customer_id = request.form.get('customer_id')
        customer_id = int(customer_id) if customer_id else None
        quantity = float(request.form.get('quantity', 1))
        payment_method = request.form.get('payment_method', 'cash')
        staff_name = request.form.get('staff_name', '')
        notes = request.form.get('notes', '')

        service = Service.query.get(service_id)
        if not service:
            return jsonify({'status': 'error', 'message': 'Invalid service'}), 400

        total = round(service.unit_price * quantity, 2)
        tx = Transaction(
            service_id=service_id, customer_id=customer_id, quantity=quantity,
            unit_price=service.unit_price, total_amount=total,
            payment_method=payment_method, staff_name=staff_name or None, notes=notes or None,
        )
        db.session.add(tx)
        if customer_id:
            cust = Customer.query.get(customer_id)
            if cust:
                cust.total_visits += 1
                cust.total_spent += total
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Transaction recorded', 'total': total})
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 400


@app.route('/api/customer', methods=['POST'])
def add_customer():
    try:
        name = request.form.get('name', '').strip()
        phone = request.form.get('phone', '').strip()
        email = request.form.get('email', '').strip()
        customer_type = request.form.get('customer_type', 'walk-in')
        if not name:
            return jsonify({'status': 'error', 'message': 'Name is required'}), 400
        c = Customer(name=name, customer_type=customer_type, phone=phone or None, email=email or None)
        db.session.add(c)
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Customer added', 'id': c.id})
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 400


@app.route('/api/insights/generate', methods=['POST'])
def gen_insights():
    try:
        insights = generate_insights()
        return jsonify({'status': 'success', 'count': len(insights)})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400


@app.route('/api/insights/<int:insight_id>/read', methods=['POST'])
def read_insight(insight_id):
    try:
        mark_read(insight_id)
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400



@app.route('/seed')
def seed_db():
    """One-time database seeding (visit this once after deployment)."""
    try:
        from models import Service
        if Service.query.count() > 0:
            return '<h3>Database already seeded.</h3><p><a href="/">Go to Dashboard</a></p>'
        from seed_data import seed_all
        seed_all()
        from analytics import compute_daily_metrics
        from datetime import date, timedelta
        for i in range(1, 61):
            d = date.today() - timedelta(days=i)
            compute_daily_metrics(d)
        return '<h3>Database seeded successfully!</h3><p><a href="/">Go to Dashboard</a></p>'
    except Exception as e:
        return f'<h3>Error: {str(e)}</h3>'


@app.route('/reset')
def reset_db():
    """Delete old database and re-seed with fresh realistic data."""
    import os as _os
    try:
        db_path = _os.path.join(_os.path.abspath(_os.path.dirname(__file__)), 'analytics.db')
        if _os.path.exists(db_path):
            _os.remove(db_path)
        db.create_all()
        from seed_data import seed_all
        seed_all()
        from analytics import compute_daily_metrics
        from datetime import date, timedelta
        for i in range(1, 61):
            d = date.today() - timedelta(days=i)
            compute_daily_metrics(d)
        return '<h3>Database reset with fresh realistic data!</h3><p><a href="/">Go to Dashboard</a></p>'
    except Exception as e:
        return f'<h3>Reset error: {str(e)}</h3>'


if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
