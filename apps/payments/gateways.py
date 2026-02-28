"""
Payment Gateway Abstraction Layer
Provides unified interface for all payment gateways
"""

from abc import ABC, abstractmethod
from decimal import Decimal
from django.conf import settings
import uuid


class PaymentGateway(ABC):
	"""Abstract base class for all payment gateways"""
	
	@abstractmethod
	def initiate_payment(self, booking, amount, user):
		"""
		Initiate payment and return payment URL or data
		Returns: dict with payment_url, transaction_id, etc.
		"""
		pass
	
	@abstractmethod
	def verify_payment(self, transaction_id, gateway_transaction_id):
		"""
		Verify payment status from gateway
		Returns: bool (success/failure), dict with status info
		"""
		pass
	
	@abstractmethod
	def process_refund(self, transaction_id, amount):
		"""
		Process refund for a transaction
		Returns: bool (success/failure), dict with refund info
		"""
		pass


class WalletGateway(PaymentGateway):
	"""ZygoTrip Wallet - Direct wallet balance payments"""
	
	def initiate_payment(self, booking, amount, user):
		"""Initiate wallet payment"""
		from apps.payments.models import WalletBalance, WalletTransaction, PaymentTransaction
		
		# Get or create wallet
		wallet, created = WalletBalance.objects.get_or_create(user=user)
		
		# Check balance
		if wallet.balance < amount:
			return {
				'success': False,
				'error': 'Insufficient wallet balance',
				'required': float(amount),
				'available': float(wallet.balance),
			}
		
		# Create payment transaction
		transaction_id = f"WLT-{uuid.uuid4().hex[:12].upper()}"
		payment_txn = PaymentTransaction.objects.create(
			transaction_id=transaction_id,
			gateway='wallet',
			user=user,
			booking_reference=str(booking.id),
			amount=amount,
			status='pending'
		)
		
		# Deduct from wallet
		try:
			balance_before = wallet.balance
			wallet.deduct(amount)
			balance_after = wallet.balance
			
			# Create wallet transaction record
			WalletTransaction.objects.create(
				wallet=wallet,
				transaction_type='debit',
				amount=amount,
				booking_reference=str(booking.id),
				description=f"Payment for booking #{booking.id}",
				balance_before=balance_before,
				balance_after=balance_after
			)
			
			# Mark payment as success
			payment_txn.mark_success(transaction_id)
			
			return {
				'success': True,
				'transaction_id': transaction_id,
				'gateway': 'wallet',
				'message': 'Payment successful from wallet'
			}
			
		except Exception as e:
			payment_txn.mark_failed(str(e))
			return {
				'success': False,
				'error': str(e)
			}
	
	def verify_payment(self, transaction_id, gateway_transaction_id=None):
		"""Verify wallet payment (always instant)"""
		from apps.payments.models import PaymentTransaction
		
		try:
			txn = PaymentTransaction.objects.get(transaction_id=transaction_id)
			return (txn.status == 'success', {'status': txn.status})
		except PaymentTransaction.DoesNotExist:
			return (False, {'error': 'Transaction not found'})
	
	def process_refund(self, transaction_id, amount):
		"""Process refund to wallet"""
		from apps.payments.models import PaymentTransaction, WalletTransaction
		
		try:
			txn = PaymentTransaction.objects.get(transaction_id=transaction_id)
			wallet = txn.user.wallet
			
			balance_before = wallet.balance
			wallet.add(amount)
			balance_after = wallet.balance
			
			# Create refund transaction record
			WalletTransaction.objects.create(
				wallet=wallet,
				transaction_type='credit',
				amount=amount,
				booking_reference=txn.booking_reference,
				description=f"Refund for booking #{txn.booking_reference}",
				balance_before=balance_before,
				balance_after=balance_after
			)
			
			txn.initiate_refund(amount)
			
			return (True, {'message': 'Refund processed successfully'})
			
		except Exception as e:
			return (False, {'error': str(e)})


class PaytmUPIGateway(PaymentGateway):
	"""Paytm UPI integration"""
	
	def initiate_payment(self, booking, amount, user):
		"""Initiate Paytm UPI payment"""
		from apps.payments.models import PaymentTransaction
		
		transaction_id = f"PTM-{uuid.uuid4().hex[:12].upper()}"
		
		# Create payment transaction
		payment_txn = PaymentTransaction.objects.create(
			transaction_id=transaction_id,
			gateway='paytm_upi',
			user=user,
			booking_reference=str(booking.id),
			amount=amount,
			status='initiated'
		)
		
		# TODO: Implement actual Paytm API integration
		# For now, return mock payment URL
		payment_url = f"https://securegw.paytm.in/order/process?txnToken=MOCK_{transaction_id}"
		
		return {
			'success': True,
			'transaction_id': transaction_id,
			'gateway': 'paytm_upi',
			'payment_url': payment_url,
			'message': 'Redirect to Paytm for UPI payment'
		}
	
	def verify_payment(self, transaction_id, gateway_transaction_id):
		"""Verify Paytm payment status"""
		# TODO: Implement Paytm verification API call
		return (False, {'error': 'Paytm verification not implemented yet'})
	
	def process_refund(self, transaction_id, amount):
		"""Process Paytm refund"""
		# TODO: Implement Paytm refund API call
		return (False, {'error': 'Paytm refund not implemented yet'})


class CashfreeGateway(PaymentGateway):
	"""Cashfree payment gateway for cards"""
	
	def initiate_payment(self, booking, amount, user):
		"""Initiate Cashfree payment"""
		from apps.payments.models import PaymentTransaction
		
		transaction_id = f"CFR-{uuid.uuid4().hex[:12].upper()}"
		
		# Create payment transaction
		payment_txn = PaymentTransaction.objects.create(
			transaction_id=transaction_id,
			gateway='cashfree',
			user=user,
			booking_reference=str(booking.id),
			amount=amount,
			status='initiated'
		)
		
		# TODO: Implement actual Cashfree API integration
		payment_url = f"https://www.cashfree.com/checkout?order_id={transaction_id}"
		
		return {
			'success': True,
			'transaction_id': transaction_id,
			'gateway': 'cashfree',
			'payment_url': payment_url,
			'message': 'Redirect to Cashfree for card payment'
		}
	
	def verify_payment(self, transaction_id, gateway_transaction_id):
		"""Verify Cashfree payment status"""
		# TODO: Implement Cashfree verification API call
		return (False, {'error': 'Cashfree verification not implemented yet'})
	
	def process_refund(self, transaction_id, amount):
		"""Process Cashfree refund"""
		# TODO: Implement Cashfree refund API call
		return (False, {'error': 'Cashfree refund not implemented yet'})


class StripeGateway(PaymentGateway):
	"""Stripe payment gateway (fallback)"""
	
	def initiate_payment(self, booking, amount, user):
		"""Initiate Stripe payment"""
		from apps.payments.models import PaymentTransaction
		
		transaction_id = f"STR-{uuid.uuid4().hex[:12].upper()}"
		
		# Create payment transaction
		payment_txn = PaymentTransaction.objects.create(
			transaction_id=transaction_id,
			gateway='stripe',
			user=user,
			booking_reference=str(booking.id),
			amount=amount,
			status='initiated'
		)
		
		# TODO: Implement actual Stripe API integration
		payment_url = f"https://checkout.stripe.com/pay/{transaction_id}"
		
		return {
			'success': True,
			'transaction_id': transaction_id,
			'gateway': 'stripe',
			'payment_url': payment_url,
			'message': 'Redirect to Stripe for payment'
		}
	
	def verify_payment(self, transaction_id, gateway_transaction_id):
		"""Verify Stripe payment status"""
		# TODO: Implement Stripe verification API call
		return (False, {'error': 'Stripe verification not implemented yet'})
	
	def process_refund(self, transaction_id, amount):
		"""Process Stripe refund"""
		# TODO: Implement Stripe refund API call
		return (False, {'error': 'Stripe refund not implemented yet'})


# Gateway routing logic
class PaymentRouter:
	"""Routes payments to appropriate gateway based on priority and availability"""
	
	@staticmethod
	def get_available_gateways(amount, user):
		"""Get list of available gateways for the given amount and user"""
		from apps.payments.models import WalletBalance
		
		gateways = []
		
		# 1. Wallet (if sufficient balance)
		try:
			wallet = WalletBalance.objects.get(user=user)
			if wallet.balance >= amount:
				gateways.append({
					'gateway': 'wallet',
					'name': 'ZygoTrip Wallet',
					'balance': float(wallet.balance),
					'priority': 1
				})
		except WalletBalance.DoesNotExist:
			pass
		
		# 2. UPI (Paytm)
		gateways.append({
			'gateway': 'paytm_upi',
			'name': 'UPI (Paytm)',
			'priority': 2
		})
		
		# 3. Cards (Cashfree)
		gateways.append({
			'gateway': 'cashfree',
			'name': 'Credit/Debit Card',
			'priority': 3
		})
		
		# 4. Stripe (fallback)
		gateways.append({
			'gateway': 'stripe',
			'name': 'International Cards (Stripe)',
			'priority': 4
		})
		
		return sorted(gateways, key=lambda x: x['priority'])
	
	@staticmethod
	def get_gateway(gateway_name):
		"""Get gateway instance by name"""
		gateways = {
			'wallet': WalletGateway(),
			'paytm_upi': PaytmUPIGateway(),
			'cashfree': CashfreeGateway(),
			'stripe': StripeGateway(),
		}
		return gateways.get(gateway_name)
