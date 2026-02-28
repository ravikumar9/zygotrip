"""
Payment Views
Handles checkout page and payment gateway webhooks
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from apps.payments.gateways import PaymentRouter
import json


@login_required
def checkout(request, booking_ref):
	"""
	Payment checkout page
	URL: /payments/checkout/<booking_ref>/
	
	Shows available payment options and allows user to select gateway
	"""
	from apps.booking.models import Booking
	
	booking = get_object_or_404(Booking, booking_number=booking_ref, user=request.user)
	
	# Check if already paid
	if booking.payment_status == 'paid':
		messages.info(request, "This booking has already been paid for")
		return redirect('booking:confirmation', booking_ref=booking_ref)
	
	# Get available payment gateways
	amount = booking.total_price
	available_gateways = PaymentRouter.get_available_gateways(amount, request.user)
	
	context = {
		'booking': booking,
		'amount': amount,
		'gateways': available_gateways,
		'title': 'Payment Checkout',
	}
	
	return render(request, 'payments/checkout.html', context)


@login_required
def initiate_payment(request, booking_ref):
	"""
	Initiate payment with selected gateway
	URL: /payments/initiate/<booking_ref>/
	"""
	from apps.booking.models import Booking
	
	if request.method != 'POST':
		return JsonResponse({'error': 'Method not allowed'}, status=405)
	
	booking = get_object_or_404(Booking, booking_number=booking_ref, user=request.user)
	
	# Get selected gateway
	gateway_name = request.POST.get('gateway')
	if not gateway_name:
		return JsonResponse({'error': 'Gateway not specified'}, status=400)
	
	# Get gateway instance
	gateway = PaymentRouter.get_gateway(gateway_name)
	if not gateway:
		return JsonResponse({'error': 'Invalid gateway'}, status=400)
	
	# Initiate payment
	result = gateway.initiate_payment(
		booking=booking,
		amount=booking.total_price,
		user=request.user
	)
	
	if result.get('success'):
		# If wallet payment or instant success
		if result.get('gateway') == 'wallet':
			booking.payment_status = 'paid'
			booking.status = 'confirmed'
			booking.save()
			
			return JsonResponse({
				'success': True,
				'redirect_url': f'/bookings/confirmation/{booking_ref}/'
			})
		else:
			# Redirect to gateway payment page
			return JsonResponse({
				'success': True,
				'payment_url': result.get('payment_url'),
				'transaction_id': result.get('transaction_id')
			})
	else:
		return JsonResponse({
			'success': False,
			'error': result.get('error', 'Payment initiation failed')
		}, status=400)


@csrf_exempt
def webhook_paytm(request):
	"""
	Paytm webhook endpoint
	URL: /payments/webhook/paytm/
	"""
	if request.method != 'POST':
		return HttpResponse(status=405)
	
	try:
		# Parse webhook data
		data = json.loads(request.body)
		
		# TODO: Verify webhook signature
		
		# Extract transaction details
		transaction_id = data.get('orderId')
		status = data.get('resultInfo', {}).get('resultStatus')
		gateway_txn_id = data.get('txnId')
		
		# Update payment transaction
		from apps.payments.models import PaymentTransaction
		txn = PaymentTransaction.objects.get(transaction_id=transaction_id)
		
		if status == 'TXN_SUCCESS':
			txn.mark_success(gateway_txn_id, gateway_response=data)
			
			# Update booking
			from apps.booking.models import Booking
			booking = Booking.objects.get(booking_number=txn.booking_reference)
			booking.payment_status = 'paid'
			booking.status = 'confirmed'
			booking.save()
		else:
			txn.mark_failed(data.get('resultInfo', {}).get('resultMsg'), gateway_response=data)
		
		return HttpResponse("OK")
		
	except Exception as e:
		return HttpResponse(f"Error: {str(e)}", status=500)


@csrf_exempt
def webhook_cashfree(request):
	"""
	Cashfree webhook endpoint
	URL: /payments/webhook/cashfree/
	"""
	if request.method != 'POST':
		return HttpResponse(status=405)
	
	try:
		# Parse webhook data
		data = json.loads(request.body)
		
		# TODO: Verify webhook signature
		
		# Extract transaction details
		transaction_id = data.get('order_id')
		status = data.get('order_status')
		gateway_txn_id = data.get('cf_order_id')
		
		# Update payment transaction
		from apps.payments.models import PaymentTransaction
		txn = PaymentTransaction.objects.get(transaction_id=transaction_id)
		
		if status == 'PAID':
			txn.mark_success(gateway_txn_id, gateway_response=data)
			
			# Update booking
			from apps.booking.models import Booking
			booking = Booking.objects.get(booking_number=txn.booking_reference)
			booking.payment_status = 'paid'
			booking.status = 'confirmed'
			booking.save()
		else:
			txn.mark_failed(f"Status: {status}", gateway_response=data)
		
		return HttpResponse("OK")
		
	except Exception as e:
		return HttpResponse(f"Error: {str(e)}", status=500)


@csrf_exempt
def webhook_stripe(request):
	"""
	Stripe webhook endpoint
	URL: /payments/webhook/stripe/
	"""
	if request.method != 'POST':
		return HttpResponse(status=405)
	
	try:
		# Parse webhook data
		data = json.loads(request.body)
		
		# TODO: Verify Stripe signature
		
		# Extract event type
		event_type = data.get('type')
		
		if event_type == 'payment_intent.succeeded':
			payment_intent = data.get('data', {}).get('object', {})
			transaction_id = payment_intent.get('metadata', {}).get('transaction_id')
			gateway_txn_id = payment_intent.get('id')
			
			# Update payment transaction
			from apps.payments.models import PaymentTransaction
			txn = PaymentTransaction.objects.get(transaction_id=transaction_id)
			txn.mark_success(gateway_txn_id, gateway_response=data)
			
			# Update booking
			from apps.booking.models import Booking
			booking = Booking.objects.get(booking_number=txn.booking_reference)
			booking.payment_status = 'paid'
			booking.status = 'confirmed'
			booking.save()
		
		elif event_type == 'payment_intent.payment_failed':
			payment_intent = data.get('data', {}).get('object', {})
			transaction_id = payment_intent.get('metadata', {}).get('transaction_id')
			
			# Update payment transaction
			from apps.payments.models import PaymentTransaction
			txn = PaymentTransaction.objects.get(transaction_id=transaction_id)
			txn.mark_failed("Payment failed", gateway_response=data)
		
		return HttpResponse("OK")
		
	except Exception as e:
		return HttpResponse(f"Error: {str(e)}", status=500)


@login_required
def payment_status(request, transaction_id):
	"""
	Check payment status
	URL: /payments/status/<transaction_id>/
	"""
	from apps.payments.models import PaymentTransaction
	
	txn = get_object_or_404(PaymentTransaction, transaction_id=transaction_id, user=request.user)
	
	return JsonResponse({
		'transaction_id': txn.transaction_id,
		'status': txn.status,
		'gateway': txn.gateway,
		'amount': float(txn.amount),
		'booking_reference': txn.booking_reference,
	})
