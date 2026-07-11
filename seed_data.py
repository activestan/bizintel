"""
Populates the database with realistic operational data for IPWEB Ventures,
a computing business hub on FUTO Road, Owerri, Imo State.
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
        ('Printing', 'Black & White Printing (A4)', 30.0, 'per_page', 'A4 B/W print per page'),
        ('Printing', 'Colour Printing (A4)', 100.0, 'per_page', 'A4 full-colour print per page'),
        ('Printing', 'Large Format (A3)', 350.0, 'per_page', 'A3 posters, banners, project covers'),
        ('Typing', 'Typing & Editing', 200.0, 'per_page', 'Document typing and formatting per page'),
        ('Typing', 'CV/Resume Design', 1500.0, 'per_project', 'Professional CV or resume design'),
        ('Typing', 'Project/Seminar Typing', 4000.0, 'per_project', 'Full project or seminar typing and binding prep'),
        ('Internet', 'Internet Browsing (30 min)', 150.0, 'per_session', '30-minute internet session'),
        ('Internet', 'Internet Browsing (1 hour)', 250.0, 'per_session', '1-hour internet session'),
        ('Photocopy', 'Photocopy B/W (A4)', 20.0, 'per_page', 'Black and white photocopy per page'),
        ('Photocopy', 'Photocopy Colour (A4)', 80.0, 'per_page', 'Colour photocopy per page'),
        ('Graphic Design', 'Logo Design', 8000.0, 'per_project', 'Custom logo design package'),
        ('Graphic Design', 'Flyer/Banner Design', 3500.0, 'per_project', 'Event flyer or promotional banner'),
        ('Training', 'Basic Computer Training', 3000.0, 'per_session', '2-hour beginners computer class'),
        ('Binding', 'Document Binding', 400.0, 'per_project', 'Spiral or thermal binding'),
        ('Lamination', 'Lamination (A4)', 200.0, 'per_page', 'A4 lamination per sheet'),
        ('Scanning', 'Document Scanning', 100.0, 'per_page', 'Scan and email per page'),
        ('Passport', 'Passport Photograph', 800.0, 'per_session', '4-copy passport photo set'),
        ('Online Registration', 'JAMB/WAEC/NYSC Registration', 1000.0, 'per_session', 'Online exam or service registration'),
    ]
    for cat, name, price, unit, desc in services:
        db.session.add(Service(name=name, category=cat, unit_price=price, unit_type=unit, description=desc))
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
        ('Desktop PC 9', 'Computer', 'available'),
        ('Desktop PC 10', 'Computer', 'available'),
        ('HP LaserJet Printer', 'Printer', 'available'),
        ('Canon Inkjet Printer', 'Printer', 'available'),
        ('Sharp Photocopier', 'Scanner', 'available'),
        ('Binding Machine', 'Equipment', 'available'),
        ('Laminator', 'Equipment', 'available'),
    ]
    for name, rtype, status in resources:
        db.session.add(Resource(name=name, resource_type=rtype, status=status))
    db.session.commit()
    print('  Seeded {} resources'.format(len(resources)))


def seed_customers():
    customers = [
        ('Adeola Ogunleye', 'registered', '08012345678', 'adeola@gmail.com'),
        ('Emeka Nwosu', 'registered', '08098765432', 'emeka.nwosu@yahoo.com'),
        ('Blessing Okonkwo', 'walk-in', '08123456789', None),
        ('Ibrahim Suleiman', 'registered', '08055551234', 'ibrahim@futo.edu.ng'),
        ('Funmilayo Adebayo', 'corporate', '08187654321', 'funmi@adebayoconsult.com'),
        ('Chidi Eze', 'walk-in', '09012345678', None),
        ('Ngozi Okafor', 'registered', '07081234567', 'ngozi.okafor@gmail.com'),
        ('Tunde Bakare', 'walk-in', '08100009999', None),
        ('Zainab Mohammed', 'registered', '08033334444', 'zainab.m@yahoo.com'),
        ('Kelechi Onuoha', 'corporate', '09087654321', 'kelly@onuohaenterprises.com'),
        ('Amina Yusuf', 'walk-in', '07055551234', None),
        ('David Okonkwo', 'registered', '08111112222', 'david.okonkwo@gmail.com'),
        ('Grace Johnson', 'walk-in', '08022223333', None),
        ('Musa Abdullahi', 'registered', '09044445555', 'musa.a@futo.edu.ng'),
        ('Ifeanyi Maduka', 'walk-in', '08166667777', None),
        ('Chisom Egbuna', 'registered', '08170001111', 'chisom@gmail.com'),
        ('Oluchi Obi', 'walk-in', '07030002222', None),
        ('Yusuf Bello', 'registered', '09020003333', 'yusufbello@yahoo.com'),
        ('Patience Udoh', 'walk-in', '08040004444', None),
        ('Samuel Kwame', 'registered', '08150005555', 'sam.kwame@gmail.com'),
    ]
    for name, ctype, phone, email in customers:
        c = Customer(name=name, customer_type=ctype, phone=phone, email=email,
                     total_visits=random.randint(2, 20), total_spent=random.uniform(800, 18000))
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

    staff_names = [
        'Uchenna', 'Chinaza', 'Fredrick', 'Ifechukwu', 'Chiziterem', 'Davies',
        'Uchenna', 'Chinaza', 'Fredrick', 'Chiziterem',  # Some appear more often
    ]

    tx_count = 0
    for days_ago in range(60, 0, -1):
        tx_date = datetime.utcnow() - timedelta(days=days_ago)
        dow = tx_date.weekday()

        # Weekdays: 20-40 tx. Weekends: 10-20 tx. Sundays slowest.
        if dow == 6:
            num_tx = random.randint(8, 15)
        elif dow >= 5:
            num_tx = random.randint(12, 22)
        else:
            num_tx = random.randint(22, 40)

        for _ in range(num_tx):
            # Realistic hour distribution: morning 9am, peak 10am-2pm, afternoon 3-5pm
            hour_weights = [0, 0, 0, 0, 0, 0, 0, 0, 1, 3, 6, 8, 8, 6, 5, 3, 2, 1, 0, 0, 0, 0, 0, 0]
            hour = random.choices(range(24), weights=hour_weights, k=1)[0]
            minute = random.randint(0, 59)
            tx_time = tx_date.replace(hour=hour, minute=minute)

            # Weight services realistically: printing/photocopy most common
            service_weights = []
            for s in services:
                if s.category == 'Printing':
                    service_weights.append(20)
                elif s.category == 'Photocopy':
                    service_weights.append(18)
                elif s.category == 'Internet':
                    service_weights.append(15)
                elif s.category == 'Typing':
                    service_weights.append(12)
                elif s.category == 'Scanning':
                    service_weights.append(8)
                elif s.category == 'Passport':
                    service_weights.append(6)
                elif s.category == 'Online Registration':
                    service_weights.append(5)
                elif s.category == 'Lamination':
                    service_weights.append(4)
                elif s.category == 'Binding':
                    service_weights.append(4)
                elif s.category == 'Graphic Design':
                    service_weights.append(3)
                elif s.category == 'Training':
                    service_weights.append(1)
                else:
                    service_weights.append(3)
            service = random.choices(services, weights=service_weights, k=1)[0]

            # Quantity: printing/photocopy = 2-10 pages typical, sometimes 20+
            if service.unit_type == 'per_page' and service.category in ['Printing', 'Photocopy']:
                quantity = random.choices([1,2,3,4,5,6,8,10,12,15,20,25], 
                                          weights=[10,15,15,12,10,8,6,4,3,2,1,1], k=1)[0]
            elif service.unit_type == 'per_page':
                quantity = random.randint(1, 5)
            else:
                quantity = 1

            total = round(service.unit_price * quantity, 2)

            customer = random.choice(customers)

            # Payment: mostly cash, some transfer, occasional POS
            payment = random.choices(['cash', 'transfer', 'POS'], weights=[55, 35, 10], k=1)[0]

            tx = Transaction(
                service_id=service.id, customer_id=customer.id,
                quantity=quantity, unit_price=service.unit_price,
                total_amount=total, payment_method=payment,
                staff_name=random.choice(staff_names),
                created_at=tx_time,
            )
            db.session.add(tx)
            tx_count += 1

            # Resource usage: only for internet sessions and some printing
            if service.category == 'Internet':
                computers = [r for r in resources if r.resource_type == 'Computer' and r.status == 'available']
                if computers:
                    res = random.choice(computers)
                    duration = 30 if '30 min' in service.name else random.choice([45, 60, 90])
                    end_time = tx_time + timedelta(minutes=duration)
                    ru = ResourceUsage(resource_id=res.id, start_time=tx_time, end_time=end_time, status='completed')
                    db.session.add(ru)
                    ru.duration_minutes = duration

            customer.total_visits += 1
            customer.total_spent += total

    db.session.commit()
    print('  Seeded {} transactions across 60 days'.format(tx_count))
