#!/usr/bin/env python
"""Proper Django auth tests using TestCase"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zygotrip_project.settings')
django.setup()

from django.test import TestCase, Client
from django.contrib.auth import get_user_model

User = get_user_model()

class AuthFlowTests(TestCase):
    """Test authentication system"""
    
    def setUp(self):
        """Create test user"""
        self.user = User.objects.create_user(
            email='test@example.com',
            full_name='Test User',
            password='TestPass123!'
        )
    
    def test_login_valid_credentials(self):
        """Test login with valid email and password"""
        response = self.client.post('/login/', {
            'username': 'test@example.com',  # CustomAuthenticationForm uses 'username' field
            'password': 'TestPass123!'
        })
        print(f'[TEST 1] Login with valid credentials')
        print(f'  Status: {response.status_code}')
        print(f'  Redirected: {response.status_code in [301, 302, 303, 307, 308]}')
        
        # Check session
        session_user_id = self.client.session.get('_auth_user_id')
        print(f'  Session user_id: {session_user_id}')
        print(f'  ✓ PASS' if session_user_id == str(self.user.id) else f'  ✗ FAIL')
        
        self.assertEqual(response.status_code, 302)  # Should redirect
        self.assertEqual(session_user_id, str(self.user.id))
    
    def test_login_invalid_credentials(self):
        """Test login with invalid password"""
        response = self.client.post('/login/', {
            'username': 'test@example.com',
            'password': 'WrongPassword123!'
        })
        print(f'[TEST 2] Login with invalid credentials')
        print(f'  Status: {response.status_code}')
        
        # Should return 200 with form errors
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'form')
        self.assertFormError(response, 'form', None, 'Please enter a correct email and password')
        print(f'  ✓ PASS')
    
    def test_register(self):
        """Test user registration"""
        response = self.client.post('/register/', {
            'email': 'newuser@example.com',
            'full_name': 'New User',
            'password1': 'NewPass123!',
            'password2': 'NewPass123!'
        })
        print(f'[TEST 3] Register new user')
        print(f'  Status: {response.status_code}')
        
        # Should redirect after successful registration
        self.assertEqual(response.status_code, 302)
        
        # User should be created
        new_user = User.objects.get(email='newuser@example.com')
        self.assertIsNotNone(new_user)
        print(f'  User created: {new_user.email}')
        print(f'  ✓ PASS')
    
    def test_home_page_field_access(self):
        """Test that home page can access user fields without errors"""
        # Login first
        self.client.login(username='test@example.com', password='TestPass123!')
        
        response = self.client.get('/')
        print(f'[TEST 4] Home page with logged-in user')
        print(f'  Status: {response.status_code}')
        
        # Should load without 500 error
        self.assertEqual(response.status_code, 200)
        print(f'  ✓ PASS')
    
    def test_logout(self):
        """Test logout"""
        # Login first
        self.client.login(username='test@example.com', password='TestPass123!')
        
        # Logout
        response = self.client.get('/accounts/logout/')
        print(f'[TEST 5] Logout')
        print(f'  Status: {response.status_code}')
        
        # Should redirect
        self.assertEqual(response.status_code, 302)
        
        # Session should be cleared
        session_user_id = self.client.session.get('_auth_user_id')
        self.assertIsNone(session_user_id)
        print(f'  ✓ PASS')


if __name__ == '__main__':
    import unittest
    
    suite = unittest.TestLoader().loadTestsFromTestCase(AuthFlowTests)
    runner = unittest.TextTestRunner(verbosity=0)
    result = runner.run(suite)
    
    # Print summary
    print()
    print(f'Tests run: {result.testsRun}')
    print(f'Failures: {len(result.failures)}')
    print(f'Errors: {len(result.errors)}')
    
    if result.failures:
        print()
        for test, traceback in result.failures:
            print(f'FAILURE: {test}')
            print(traceback)
    
    if result.errors:
        print()
        for test, traceback in result.errors:
            print(f'ERROR: {test}')
            print(traceback)
