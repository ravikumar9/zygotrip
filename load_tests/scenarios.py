"""
Advanced load testing scenarios for Zygotrip.
Separate test files for different load profiles and scenarios.
"""

from locust import HttpUser, TaskSet, task, between, constant
import random
from datetime import datetime, timedelta


# ==========================================
# STRESS TEST SCENARIO
# ==========================================

class StressTestTasks(TaskSet):
    """Stress test with rapid requests to identify breaking points"""
    
    @task
    def rapid_hotel_search(self):
        """Rapid hotel search requests"""
        for _ in range(10):
            self.client.get('/hotels/', allow_redirects=False)
    
    @task
    def rapid_detail_views(self):
        """Rapid detail page loads"""
        for i in range(1, 6):
            self.client.get(f'/hotels/{i}/', allow_redirects=False)


class StressTestUser(HttpUser):
    """User for stress testing"""
    tasks = [StressTestTasks]
    wait_time = constant(0.5)  # 500ms between requests


# ==========================================
# SPIKE TEST SCENARIO
# ==========================================

class SpikeTestTasks(TaskSet):
    """Spike test with sudden load increase"""
    
    @task(5)
    def search(self):
        self.client.get('/hotels/')
    
    @task(3)
    def detail(self):
        self.client.get(f'/hotels/{random.randint(1, 5)}/')
    
    @task(1)
    def booking(self):
        self.client.get('/booking/')


class SpikeTestUser(HttpUser):
    """User for spike testing"""
    tasks = [SpikeTestTasks]
    wait_time = between(0, 2)


# ==========================================
# ENDURANCE TEST SCENARIO
# ==========================================

class EnduranceTestTasks(TaskSet):
    """Endurance test with sustained load over long period"""
    
    def on_start(self):
        self.request_count = 0
    
    @task(3)
    def normal_search(self):
        """Normal search behavior"""
        self.client.get('/hotels/')
        self.request_count += 1
    
    @task(2)
    def detail_view(self):
        """View hotel details"""
        self.client.get(f'/hotels/{random.randint(1, 10)}/')
        self.request_count += 1
    
    @task(1)
    def occasional_booking(self):
        """Occasional booking attempts"""
        if random.random() < 0.1:  # 10% chance
            self.client.get('/booking/')
        self.request_count += 1


class EnduranceTestUser(HttpUser):
    """User for endurance testing"""
    tasks = [EnduranceTestTasks]
    wait_time = between(2, 5)


# ==========================================
# CACHE EFFECTIVENESS TEST
# ==========================================

class CacheTestTasks(TaskSet):
    """Test cache hit rates with repeated searches"""
    
    def on_start(self):
        self.search_queries = [
            {'location': 'Delhi', 'guests': 2},
            {'location': 'Mumbai', 'guests': 3},
            {'location': 'Bangalore', 'guests': 2},
        ]
    
    @task
    def repeated_search(self):
        """Repeat same searches to test cache"""
        query = random.choice(self.search_queries)
        self.client.get('/hotels/', params=query)
    
    @task
    def cache_busting(self):
        """Occasional searches that might bust cache"""
        query = {
            'location': random.choice(['Delhi', 'Mumbai', 'Bangalore', 'Goa']),
            'guests': random.randint(1, 6),
        }
        self.client.get('/hotels/', params=query)


class CacheTestUser(HttpUser):
    """User for cache effectiveness testing"""
    tasks = [CacheTestTasks]
    wait_time = between(1, 3)


# ==========================================
# OPERATOR CONCURRENT EDITS TEST
# ==========================================

class ConcurrentEditsTestTasks(TaskSet):
    """Test concurrent edits to operator resources"""
    
    def on_start(self):
        # Login as operator
        email = f'bus_operator_{random.randint(1, 3)}@test.com'
        self.client.post(
            '/accounts/login/',
            {'username': email, 'password': 'Test@123'},
            allow_redirects=True
        )
        self.bus_id = 1
    
    @task(5)
    def view_resource(self):
        """View resource frequently"""
        self.client.get(f'/buses/{self.bus_id}/')
    
    @task(2)
    def update_availability(self):
        """Attempt to update availability"""
        self.client.post(
            f'/buses/{self.bus_id}/update-availability/',
            {'available': random.choice([True, False])},
            allow_redirects=True
        )


class ConcurrentEditsUser(HttpUser):
    """User for concurrent edits testing"""
    tasks = [ConcurrentEditsTestTasks]
    wait_time = between(0.5, 2)


# ==========================================
# BOOKING PIPELINE TEST
# ==========================================

class BookingPipelineTestTasks(TaskSet):
    """Test complete booking pipeline under load"""
    
    def on_start(self):
        # Login
        self.client.post(
            '/accounts/login/',
            {'username': 'customer@test.com', 'password': 'Test@123'},
            allow_redirects=True
        )
        self.session_id = random.randint(1, 1000)
    
    @task
    def complete_pipeline(self):
        """Attempt complete booking pipeline"""
        property_id = random.randint(1, 5)
        
        # Step 1: View property
        r1 = self.client.get(f'/hotels/{property_id}/')
        if r1.status_code != 200:
            return
        
        # Step 2: Initiate booking
        booking_data = {
            'property': property_id,
            'room_type': 1,
            'check_in': (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'),
            'check_out': (datetime.now() + timedelta(days=3)).strftime('%Y-%m-%d'),
            'quantity': 1,
            'guest_full_name': f'Test User {self.session_id}',
            'guest_age': random.randint(20, 60),
        }
        
        r2 = self.client.post('/booking/create/', booking_data, allow_redirects=True)
        
        # Don't continue with payment (just test flow up to review)
        return r2.status_code


class BookingPipelineUser(HttpUser):
    """User for booking pipeline testing"""
    tasks = [BookingPipelineTestTasks]
    wait_time = between(3, 8)
