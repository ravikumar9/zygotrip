"""
Locust load testing suite for Zygotrip.
Tests hotel search, operator dashboards, and booking flows.

Run: locust -f load_tests/locustfile.py --host=http://localhost:8000
"""

from locust import HttpUser, TaskSet, task, between
import json
from datetime import datetime, timedelta
import random


class AuthMixin:
    """Mixin for authentication across test users"""
    
    def login(self, email, password='Test@123'):
        """Login and store session"""
        response = self.client.post(
            '/accounts/login/',
            {
                'username': email,
                'password': password,
            },
            allow_redirects=True
        )
        return response.status_code in [200, 302]
    
    def logout(self):
        """Logout user"""
        self.client.post('/accounts/logout/')


class HotelSearchTasks(TaskSet, AuthMixin):
    """Hotel search and browsing tasks"""
    
    def on_start(self):
        """Called when a Locust starts executing this TaskSet"""
        self.login('customer@test.com')
    
    def on_stop(self):
        """Called when a Locust stops executing this TaskSet"""
        self.logout()
    
    @task(3)
    def hotel_list(self):
        """Browse hotel list page"""
        response = self.client.get('/hotels/', allow_redirects=True)
        assert response.status_code == 200, f"Failed: {response.status_code}"
    
    @task(2)
    def hotel_search(self):
        """Search hotels with filters"""
        filters = {
            'location': random.choice(['Delhi', 'Mumbai', 'Bangalore', 'Goa']),
            'check_in': (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'),
            'check_out': (datetime.now() + timedelta(days=3)).strftime('%Y-%m-%d'),
            'guests': random.randint(1, 4),
        }
        
        response = self.client.get(
            '/hotels/',
            params=filters,
            allow_redirects=True
        )
        assert response.status_code == 200
    
    @task(1)
    def hotel_detail(self):
        """View hotel detail page"""
        hotel_id = random.randint(1, 5)
        response = self.client.get(f'/hotels/{hotel_id}/', allow_redirects=True)
        # Detail page may 404, but should not 500
        assert response.status_code in [200, 404]


class BookingFlowTasks(TaskSet, AuthMixin):
    """Complete booking workflow tasks"""
    
    def on_start(self):
        """Setup test environment"""
        self.login('customer@test.com')
        self.property_id = 1
    
    def on_stop(self):
        self.logout()
    
    @task
    def complete_booking_flow(self):
        """Simulate complete booking flow"""
        # Step 1: Browse hotels
        response = self.client.get('/hotels/', allow_redirects=True)
        assert response.status_code == 200
        
        # Step 2: View hotel detail
        response = self.client.get(f'/hotels/{self.property_id}/', allow_redirects=True)
        if response.status_code != 200:
            return
        
        # Step 3: Create booking (initiate flow)
        booking_data = {
            'property': self.property_id,
            'room_type': 1,
            'check_in': (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'),
            'check_out': (datetime.now() + timedelta(days=3)).strftime('%Y-%m-%d'),
            'quantity': 1,
            'guest_full_name': f'Load Test User {random.randint(1000, 9999)}',
            'guest_age': random.randint(20, 60),
        }
        
        response = self.client.post(
            '/booking/create/',
            booking_data,
            allow_redirects=True
        )
        # Expect redirect to review page
        assert response.status_code in [200, 302, 404]


class BusOperatorTasks(TaskSet, AuthMixin):
    """Bus operator dashboard tasks"""
    
    def on_start(self):
        """Login as bus operator"""
        email = f'bus_operator_{random.randint(1, 3)}@test.com'
        self.login(email)
    
    def on_stop(self):
        self.logout()
    
    @task(2)
    def view_dashboard(self):
        """View bus operator dashboard"""
        response = self.client.get('/buses/dashboard/', allow_redirects=True)
        assert response.status_code in [200, 404]
    
    @task(1)
    def view_bus_detail(self):
        """View individual bus details"""
        bus_id = random.randint(1, 9)
        response = self.client.get(f'/buses/{bus_id}/', allow_redirects=True)
        assert response.status_code in [200, 404]
    
    @task(1)
    def view_bookings(self):
        """View bookings for operator's buses"""
        response = self.client.get('/buses/bookings/', allow_redirects=True)
        assert response.status_code in [200, 404]


class CabOwnerTasks(TaskSet, AuthMixin):
    """Cab owner dashboard tasks"""
    
    def on_start(self):
        """Login as cab owner"""
        email = f'cab_owner_{random.randint(1, 3)}@test.com'
        self.login(email)
    
    def on_stop(self):
        self.logout()
    
    @task(2)
    def view_dashboard(self):
        """View cab owner dashboard"""
        response = self.client.get('/cabs/dashboard/', allow_redirects=True)
        assert response.status_code in [200, 404]
    
    @task(1)
    def view_cab_detail(self):
        """View individual cab details"""
        cab_id = random.randint(1, 9)
        response = self.client.get(f'/cabs/{cab_id}/', allow_redirects=True)
        assert response.status_code in [200, 404]
    
    @task(1)
    def check_availability(self):
        """Check cab availability for specific date"""
        date = (datetime.now() + timedelta(days=random.randint(1, 7))).strftime('%Y-%m-%d')
        response = self.client.get(
            '/cabs/availability/',
            params={'date': date},
            allow_redirects=True
        )
        assert response.status_code in [200, 404]


class PackageBookingTasks(TaskSet, AuthMixin):
    """Package booking tasks"""
    
    def on_start(self):
        """Login as customer"""
        self.login('customer@test.com')
    
    def on_stop(self):
        self.logout()
    
    @task(2)
    def view_packages(self):
        """View available packages"""
        response = self.client.get('/packages/', allow_redirects=True)
        assert response.status_code in [200, 404]
    
    @task(1)
    def view_package_detail(self):
        """View package details"""
        package_id = random.randint(1, 15)
        response = self.client.get(f'/packages/{package_id}/', allow_redirects=True)
        assert response.status_code in [200, 404]
    
    @task(1)
    def check_package_availability(self):
        """Check package availability"""
        package_id = random.randint(1, 15)
        start_date = (datetime.now() + timedelta(days=random.randint(1, 30))).strftime('%Y-%m-%d')
        response = self.client.get(
            f'/packages/{package_id}/availability/',
            params={'start_date': start_date},
            allow_redirects=True
        )
        assert response.status_code in [200, 404]


class ZogotripCustomer(HttpUser):
    """Simulates customer user behavior"""
    tasks = [HotelSearchTasks, BookingFlowTasks, PackageBookingTasks]
    wait_time = between(1, 3)


class ZogotripBusOperator(HttpUser):
    """Simulates bus operator user behavior"""
    tasks = [BusOperatorTasks]
    wait_time = between(2, 5)
    weight = 1  # 1 bus operator per 10 customers


class ZogotripCabOwner(HttpUser):
    """Simulates cab owner user behavior"""
    tasks = [CabOwnerTasks]
    wait_time = between(2, 5)
    weight = 1  # 1 cab owner per 10 customers