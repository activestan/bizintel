INTELLIGENT BUSINESS ANALYTICS SYSTEM
Optimising Operations in a Computing Business Hub
===================================================

HOW TO RUN:
  1. Install Python 3.9+ on your computer
  2. Open terminal/command prompt in this folder
  3. Run: pip install -r requirements.txt
  4. Run: python app.py
  5. Open browser: http://localhost:5000

The database auto-seeds with 60 days of demo data on first run.

PAGES:
  /             Dashboard (KPIs, charts, insights)
  /analytics    Detailed analytics & customer metrics
  /predictions  Demand & resource forecasts
  /insights     Decision support recommendations
  /data-entry   Transaction recording & customer management

FILES:
  app.py              Main Flask application
  models.py           Database models (SQLite via SQLAlchemy)
  analytics.py        Analytics engine (KPIs, trends, metrics)
  predictive.py       Forecasting engine (scikit-learn)
  decision_support.py Decision support engine (6 rules)
  seed_data.py        Demo data generator
  requirements.txt    Python dependencies
  templates/          HTML templates (Jinja2)
