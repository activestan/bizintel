"""
Populates the database with sample operational data for a computing business hub.
"""
import random
from datetime import datetime, date, timedelta
from models import db, Service, Resource, Customer, Transaction, ResourceUsage


def seed_all():
    seed_services()
    seed_resources()
    seed_customers()
    seed_transactions()


def seed_services():
    services = [
        ('Printing', 'Black & White Printing', 50.0, 'per_page', 'A4 B/W print per page'),
        ('Printing', 'Colour Printing', 150.0, 'per_page', 'A4 colour print per page'),
        ('Printing', 'Large Format Printing', 500.0, 'per_page', 'A3/A2 posters and banners'),
        ('Typing', 'Typing & Editing', 300.0, 'per_page', 'Document typing per page'),
        ('Typing', 'CV/Resume Design', 2000.0, 'per_project', 'Professional CV design'),
        ('Internet', 'Internet Browsing (30 min)', 200.0, 'per_session', '30-minute session'),
        ('Internet', 'Internet Browsing (1 hour)', 350.0, 'per_session', '1-hour session'),
        ('Photocopy', 'Photocopy (B/W)', 30.0, 'per_page', 'B/W photocopy per page'),
        ('Photocopy', 'Photocopy (Colour)', 100.0, 'per_page', 'Colour photocopy per page'),
        ('Graphic Design', 'Logo Design', 10000.0, 'per_project', 'Custom logo design'),
        ('Graphic Design', 'Flyer/Banner Design', 5000.0, 'per_project', 'Promotional flyer or banner'),
        ('Training', 'Basic Computer Training', 5000.0, 'per_session', '2-hour basic computer class'),
        ('Training', 'Advanced Excel Training', 8000.0, 'per_session', '3-hour advanced Excel session'),
        ('Binding', 'Document Binding', 500.0, 'per_project', 'Spiral/thermal binding'),
        ('Lamination', 'Lamination (A4)', 300.0, 'per_page', 'A4 lamination per sheet'),
        ('Scanning', 'Document Scanning', 100.0, 'per_page', 'Scan and email per page'),
        ('Registration', 'CAC Business Registration', 25000.0, 'per_project', 'Business name registration'),
        ('Passport', 'Passport Photograph', 1000.0, 'per_session', '4-copy passport photo set'),
    ]
    for cat, name, price, unit, desc in services:
        s = Service(name=name, category=cat, unit_price=price, unit_type=unit, description=desc)
        db.session.add(s)
    db.session.commit()
    print('  Seeded {} services'.format(len(services)))


def seed_resources():
    resources = [
        ('Desktop PC 1', 'Computer', 'available'),
        ('Desktop PC 2', 'Computer', 'available'),
        ('Desktop PC 3', 'Computer', 'available'),
        ('Desktop PC 4', 'Computer', 'available'),
        ('Desktop PC 5', 'Computer', 'available'),
        ('Desktop PC 6', 'Computer', 'in_use'),
        ('Desktop PC 7', 'Computer', 'available'),
        ('Desktop PC 8', 'Computer', 'maintenance'),
        ('HP LaserJet Printer', 'Printer', 'available'),
        ('Canon Colour Printer', 'Printer', 'available'),
        ('Photocopier Sharp MX', 'Scanner', 'available'),
        ('Binding Machine', 'Equipment', 'available'),
        ('Laminator', 'Equipment', 'available'),
    ]
    for name, rtype, status in resources:
        r = Resource(name=name, resource_type=rtype, status=status)
        db.session.add(r)
    db.session.commit()
    print('  Seeded {} resources'.format(len(resources)))


def seed_customers():
    customers = [
        ('Adeola Ogunleye', 'registered', '08012345678', 'adeola@email.com'),
        ('Emeka Nwosu', 'registered', '08098765432', 'emeka@email.com'),
        ('Blessing Okonkwo', 'walk-in', '08123456789', None),
        ('Ibrahim Suleiman', 'registered', '08055551234', 'ibrahim@email.com'),
        ('Funmilayo Adebayo', 'corporate', '08187654321', 'funmi@company.com'),
        ('Chidi Eze', 'walk-in', '09012345678', None),
        ('Ngozi Okafor', 'registered', '07081234567', 'ngozi@email.com'),
        ('Tunde Bakare', 'walk-in', '08100009999', None),
        ('Zainab Mohammed', 'registered', '08033334444', 'zainab@email.com'),
        ('Kelechi Onuoha', 'corporate', '09087654321', 'kelly@firm.com'),
        ('Amina Yusuf', 'walk-in', '07055551234', None),
        ('David Okonkwo', 'registered', '08111112222', 'david@email.com'),
        ('Grace Johnson', 'walk-in', '08022223333', None),
        ('Musa Abdullahi', 'registered', '09044445555', 'musa@email.com'),
        ('Ifeanyi Maduka', 'walk-in', '08166667777', None),
    ]
    for name, ctype, phone, email in customers:
        c = Customer(name=name, customer_type=ctype, phone=phone, email=email,
                     total_visits=random.randint(1, 15), total_spent=random.uniform(500, 15000))
        db.session.add(c)
    db.session.commit()
    print('  Seeded {} customers'.format(len(customers)))


def seed_transactions():
    services = Service.query.all()
    customers = Customer.query.all()
    resources = Resource.query.all()
    if not services or not customers:
        print('  No services or customers, skipping transactions')
        return

    tx_count = 0
    for days_ago in range(60, 0, -1):
        tx_date = datetime.utcnow() - timedelta(days=days_ago)
        dow = tx_date.weekday()
        num_tx = random.randint(8, 15) if dow >= 5 else random.randint(15, 35)

        for _ in range(num_tx):
            hour = random.randint(10, 14) if random.random() < 0.5 else random.choice([8, 9, 15, 16, 17])
            minute = random.randint(0, 59)
            tx_time = tx_date.replace(hour=hour, minute=minute)

            service = random.choice(services)
            quantity = random.randint(1, 5) if service.unit_type == 'per_page' else 1
            unit_price = service.unit_price * random.uniform(0.9, 1.1)
            total = round(unit_price * quantity, 2)

            customer = random.choice(customers)
            payment = random.choice(['cash', 'cash', 'cash', 'transfer', 'POS'])

            tx = Transaction(
                service_id=service.id, customer_id=customer.id,
                quantity=quantity, unit_price=round(unit_price, 2),
                total_amount=total, payment_method=payment,
                staff_name=random.choice(['Sarah', 'John', 'Hassan', 'Maryam', 'Peter']),
                created_at=tx_time,
            )
            db.session.add(tx)
            tx_count += 1

            if random.random() < 0.5:
                computers = [r for r in resources if r.resource_type == 'Computer']
                if computers:
                    res = random.choice(computers)
                    end_time = tx_time + timedelta(minutes=random.randint(15, 120))
                    ru = ResourceUsage(resource_id=res.id, start_time=tx_time, end_time=end_time, status='completed')
                    db.session.add(ru)
                    ru.duration_minutes = int((end_time - tx_time).total_seconds() / 60)

            customer.total_visits += 1
            customer.total_spent += total

    db.session.commit()
    print('  Seeded {} transactions across 60 days'.format(tx_count))
