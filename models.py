"""
Database models for the business analytics system.
"""
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class Service(db.Model):
    __tablename__ = 'services'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    unit_type = db.Column(db.String(30), nullable=False)
    description = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    transactions = db.relationship('Transaction', backref='service', lazy=True)


class Resource(db.Model):
    __tablename__ = 'resources'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    resource_type = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), default='available')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    usage_logs = db.relationship('ResourceUsage', backref='resource', lazy=True)


class Customer(db.Model):
    __tablename__ = 'customers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    customer_type = db.Column(db.String(30), default='walk-in')
    phone = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(100), nullable=True)
    total_visits = db.Column(db.Integer, default=0)
    total_spent = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    transactions = db.relationship('Transaction', backref='customer', lazy=True)


class Transaction(db.Model):
    __tablename__ = 'transactions'
    id = db.Column(db.Integer, primary_key=True)
    service_id = db.Column(db.Integer, db.ForeignKey('services.id'), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=True)
    quantity = db.Column(db.Float, nullable=False, default=1.0)
    unit_price = db.Column(db.Float, nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(30), default='cash')
    staff_name = db.Column(db.String(100), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class ResourceUsage(db.Model):
    __tablename__ = 'resource_usage'
    id = db.Column(db.Integer, primary_key=True)
    resource_id = db.Column(db.Integer, db.ForeignKey('resources.id'), nullable=False)
    transaction_id = db.Column(db.Integer, db.ForeignKey('transactions.id'), nullable=True)
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime, nullable=True)
    duration_minutes = db.Column(db.Integer, nullable=True)
    status = db.Column(db.String(20), default='active')


class OperationalMetric(db.Model):
    __tablename__ = 'operational_metrics'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, unique=True)
    total_revenue = db.Column(db.Float, default=0.0)
    total_transactions = db.Column(db.Integer, default=0)
    unique_customers = db.Column(db.Integer, default=0)
    avg_transaction_value = db.Column(db.Float, default=0.0)
    peak_hour = db.Column(db.Integer, nullable=True)
    resource_utilization_pct = db.Column(db.Float, default=0.0)
    top_service_id = db.Column(db.Integer, nullable=True)


class ForecastResult(db.Model):
    __tablename__ = 'forecast_results'
    id = db.Column(db.Integer, primary_key=True)
    forecast_type = db.Column(db.String(50), nullable=False)
    forecast_date = db.Column(db.Date, nullable=False)
    predicted_value = db.Column(db.Float, nullable=False)
    confidence_lower = db.Column(db.Float, nullable=True)
    confidence_upper = db.Column(db.Float, nullable=True)
    model_used = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class EfficiencyInsight(db.Model):
    __tablename__ = 'efficiency_insights'
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(50), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    severity = db.Column(db.String(20), default='info')
    metric_name = db.Column(db.String(50), nullable=True)
    metric_value = db.Column(db.Float, nullable=True)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
