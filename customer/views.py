from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render

from common.models import Customer
from seller.models import Product
from customer.models import Cart,Order,OrderItem

from django.shortcuts import get_object_or_404
from django.contrib.auth import logout
from django.db import transaction
from django.contrib import messages
import datetime  
from seller.decorators import auth_customer
from django.db.models import Q
from django.template.loader import render_to_string
from django.db import connection
from django.conf import settings
import time
import os  
import razorpay
from decimal import Decimal
from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError





@auth_customer
def customer_home(request):
    # 1. Fetch only Best Sellers
    new_arrivals = Product.objects.filter(best_seller='Yes').order_by('-id')
    
    # 2. Session Security Check
    customer_id = request.session.get('customer')
    if not customer_id:
        return redirect('common:customer_login')
    
    
    # 3. Secure Customer Retrieval
    try:
        customer = Customer.objects.get(id=customer_id)
        cust_nm = customer.c_name
    except Customer.DoesNotExist:
        # If session is invalid, clear it and redirect
        request.session.flush()
        return redirect('common:customer_login')
    
    recently_viewed_ids = request.session.get('recently_viewed', [])
    recently_viewed_products = []

    if recently_viewed_ids:
        # Fetch products matching the IDs preserved in the session
        products_queryset = Product.objects.filter(id__in=recently_viewed_ids)
        
        # Sort them in the exact order they appear in the session list (most recent first)
        product_map = {p.id: p for p in products_queryset}
        recently_viewed_products = [product_map[p_id] for p_id in recently_viewed_ids if p_id in product_map]

    context = {
        'new_arrvl': new_arrivals,
        'name': cust_nm,
        'recently_viewed': recently_viewed_products,
    }
    
    return render(request, 'customer/customer_home.html', context)

@auth_customer
def customer_home_filter(request,cat_id):
    if(cat_id == 1):
        prod = Product.objects.filter(p_genre = 'Fiction')
    elif(cat_id == 2):
        prod = Product.objects.filter(p_genre = 'Self-Help')
    else:
        prod = Product.objects.filter(p_genre = 'Biography')
    return render(request, 'customer/customer_home.html',{'prdct': prod})

def search_books(request):
    query = request.GET.get("q", "")
    if query:
        books = Product.objects.filter(p_name__icontains=query)[:10]
        results = [
            {"id": b.id, "name": b.p_name}
            for b in books
        ]
    else:
        results = []
    return JsonResponse({"results": results})







@auth_customer
def product_details(request, pid):
    product = get_object_or_404(Product, id=pid)
    related_products = Product.objects.filter(p_genre=product.p_genre).exclude(id=pid)[:4]
    
    # Check if the product is already in the user's cart
    is_in_cart = False
    if 'customer' in request.session:
        is_in_cart = Cart.objects.filter(
            customer_id=request.session['customer'], 
            product_id=pid
        ).exists()
    
    context = {
        'product': product,
        'related': related_products,
        'is_in_cart': is_in_cart # Pass this to the template
    }
    if 'recently_viewed' not in request.session:
        request.session['recently_viewed'] = []
    
    # 2. Get the existing list safely
    recently_viewed_ids = request.session['recently_viewed']
    
    # 3. Clean-up logic: If the product is already in the list, remove it first (to bring it to the front)
    if pid in recently_viewed_ids:
        recently_viewed_ids.remove(pid)
        
    # 4. Insert the product ID at the very beginning of the list
    recently_viewed_ids.insert(0, pid)
    
    # 5. Limit the list to the last 10 items so it stays clean
    request.session['recently_viewed'] = recently_viewed_ids[:10]
    
    # Tell Django the session data has been updated
    request.session.modified = True
    
    # Recommended: ensure your filename is product_details.html (with underscore)
    return render(request, 'customer/product details.html', context)


@auth_customer
def customer_changepassword(request):
    msg = ''

    if request.method == "POST":
        oldpassword = request.POST.get('old_password', '')
        newpassword = request.POST.get('new_password', '')
        customer = Customer.objects.get(id=request.session['customer'])

        if not check_password(oldpassword, customer.c_password):
            msg = 'Current password is incorrect.'
        else:
            try:
                validate_password(newpassword)
            except ValidationError as error:
                msg = ' '.join(error.messages)
            else:
                customer.c_password = make_password(newpassword)
                customer.save(update_fields=['c_password'])
                request.session.cycle_key()
                msg = 'Password updated successfully.'

    return render(
        request,
        'customer/change password.html',
        {'message': msg},
    )

@auth_customer
def customer_profile(request):
    customer = Customer.objects.get(id=request.session['customer'])
    return render(request, 'customer/customer_profile.html', {'customer_profile': customer})

@auth_customer
def cust_view_prod(request):
    query = request.GET.get('q', '').strip()
    genre = request.GET.get('genre')
    request_type = request.GET.get('type') # 'live' or 'filter'

    products = Product.objects.all().order_by('-id')

    if query:
        products = products.filter(
            Q(p_name__icontains=query) | Q(p_author__icontains=query) | Q(p_genre__icontains=query)
        )
    
    if genre and genre != 'all':
        products = products.filter(p_genre=genre)

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        # CASE 1: Live Recommendations (Dropdown)
        if request_type == 'live':
            html = render_to_string('customer/includes/search_results_partial.html', {'products': products[:6]})
            return JsonResponse({'html': html})
        
        # CASE 2: Main Grid Update (Filtering/Submit)
        html = render_to_string('customer/includes/product_grid_partial.html', {'products': products})
        return JsonResponse({'html': html, 'count': products.count()})

    return render(request, 'customer/cust_view_prod.html', {'products': products, 'query': query})

@auth_customer
def master_customer(request):
    customer = Customer.objects.get(id=request.session['customer'])
    cust_nm = customer.c_name
    # count = Cart_items.objects.count()
    return render(request, 'customer/master_customer.html')

def customer_logout(request):
    # Using a try-except block to handle the lock gracefully
    try:
        # 1. Clear the custom session key
        if 'customer' in request.session:
            del request.session['customer']
        
        # 2. Use built-in logout to clear all session data/cookies
        logout(request)
        
        # 3. Explicitly flush if logout didn't catch everything
        request.session.flush()
        
    except Exception:
        # If the DB is locked, we still want to redirect the user
        # The session will eventually expire or be cleared
        pass
        
    return redirect('common:customer_login')


    
        


# def payment_failed(request):
#     messages.error(
#         request,
#         "Payment was not completed. Please check your order status "
#         "before trying again and again."
#     )
#     return redirect('customer:myorders')


import json
import uuid
import logging
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from .forms import CheckoutForm
from . import checkout_service as payments

logger = logging.getLogger(__name__)

# Cart writes are POST requests and always restricted to the session customer.
@auth_customer
@require_POST
def add_to_cart(request, pid):
    customer_id = request.session['customer']
    with transaction.atomic():
        Customer.objects.select_for_update().get(pk=customer_id)
        product = get_object_or_404(Product, pk=pid)
        if product.p_stock < 1:
            messages.warning(request, 'This book is currently out of stock.')
        elif Cart.objects.filter(customer_id=customer_id, product_id=pid).exists():
            messages.info(request, 'This book is already in your cart.')
        else:
            Cart.objects.create(customer_id=customer_id, product=product, quantity=1)
            messages.success(request, 'Book added to your cart.')
    return redirect('customer:view_cart')


@auth_customer
def view_cart(request):
    customer_id = request.session['customer']
    payments.expire_reservations(customer_id)
    items = list(Cart.objects.filter(customer_id=customer_id).select_related('product').order_by('pk'))
    return render(request, 'customer/my cart.html', {
        'cart_items': items,
        'grand_total': sum((item.total_price for item in items), Decimal('0.00')),
    })


@auth_customer
@require_POST
def update_cart_quantity(request):
    customer_id = request.session['customer']
    try:
        cart_id = int(request.POST.get('cart_id', ''))
    except (TypeError, ValueError):
        return JsonResponse({'status': 'error', 'message': 'Invalid cart item.'}, status=400)
    action = request.POST.get('action')
    if action not in ['plus', 'minus']:
        return JsonResponse({'status': 'error', 'message': 'Invalid quantity action.'}, status=400)
    with transaction.atomic():
        Customer.objects.select_for_update().get(pk=customer_id)
        item = get_object_or_404(Cart.objects.select_related('product'), pk=cart_id, customer_id=customer_id)
        quantity = item.quantity + (1 if action == 'plus' else -1)
        if quantity < 1:
            return JsonResponse({'status': 'error', 'message': 'Minimum quantity is one.'}, status=400)
        if action == 'plus' and quantity > item.product.p_stock:
            return JsonResponse({'status': 'error', 'message': 'Not enough available stock. An active checkout may be reserving copies.'}, status=409)
        item.quantity = quantity
        item.save(update_fields=['quantity', 'updated_at'])
        total = sum((row.total_price for row in Cart.objects.filter(customer_id=customer_id).select_related('product')), Decimal('0.00'))
    return JsonResponse({
        'status': 'success', 'qty': item.quantity,
        'item_total': f'{item.total_price:.2f}', 'grand_total': f'{total:.2f}',
    })


@auth_customer
@require_POST
def remove_from_cart(request, cart_id):
    with transaction.atomic():
        Customer.objects.select_for_update().get(pk=request.session['customer'])
        item = get_object_or_404(Cart, pk=cart_id, customer_id=request.session['customer'])
        item.delete()
    messages.success(request, 'Book removed from your cart.')
    return redirect('customer:view_cart')


def _checkout_context(request, form):
    items = list(Cart.objects.filter(customer_id=request.session['customer']).select_related('product'))
    return {
        'form': form, 'cart_items': items,
        'grand_total': sum((item.total_price for item in items), Decimal('0.00')),
        'profile': get_object_or_404(Customer, pk=request.session['customer']),
    }


@auth_customer
def checkout(request):
    payments.expire_reservations(request.session['customer'])
    # A token identifies a single form submission, including a repeated POST.
    token = str(uuid.uuid4())
    request.session['checkout_token'] = token
    profile = get_object_or_404(Customer, pk=request.session['customer'])
    form = CheckoutForm(initial={
        'checkout_token': token, 'full_name': profile.c_name,
        'email': profile.c_email, 'address': getattr(profile, 'c_address', ''),
    })
    context = _checkout_context(request, form)
    if not context['cart_items']:
        messages.warning(request, 'Your cart is empty.')
        return redirect('customer:view_cart')
    return render(request, 'customer/checkout.html', context)


@auth_customer
@require_POST
def place_order(request):
    form = CheckoutForm(request.POST)
    if not form.is_valid():
        return render(request, 'customer/checkout.html', _checkout_context(request, form), status=400)
    # Existing owned tokens are safe to replay even if another tab opened checkout.
    token = form.cleaned_data['checkout_token']
    existing = Order.objects.filter(customer_id=request.session['customer'], checkout_token=token).first()
    if existing:
        return _order_destination(existing)
    if str(token) != request.session.get('checkout_token'):
        form.add_error(None, 'This checkout form has expired. Reload checkout and try again.')
        return render(request, 'customer/checkout.html', _checkout_context(request, form), status=400)
    try:
        order, created = payments.create_checkout(request.session['customer'], form.cleaned_data)
    except payments.CheckoutProblem as error:
        form.add_error(None, str(error))
        return render(request, 'customer/checkout.html', _checkout_context(request, form), status=409)
    if created:
        order = payments.initialize_gateway(order)
    return _order_destination(order)


def _order_destination(order):
    if order.is_paid and order.payment_status != 'Review':
        return redirect('customer:order_success', order_id=order.order_id)
    if order.payment_status == 'Pending' and order.razorpay_order_id:
        return redirect('customer:payment', order_id=order.order_id)
    return redirect('customer:payment', order_id=order.order_id)


def _owned_order(request, order_id):
    return get_object_or_404(Order, order_id=order_id, customer_id=request.session['customer'])


@auth_customer
def payment(request, order_id):
    payments.expire_reservations(request.session['customer'])
    order = _owned_order(request, order_id)
    if order.is_paid or order.payment_status != 'Pending' or not order.razorpay_order_id:
        return _order_destination(order)
    return render(request, 'customer/payment.html', {
        'order': order,
        'payment_options': {
            'key': settings.RAZORPAY_KEY_ID, 'amount': payments.amount_paise(order),
            'currency': 'INR', 'name': 'KitabHub', 'order_id': order.razorpay_order_id,
            'prefill': {'name': order.full_name, 'email': order.email},
            'theme': {'color': '#064e3b'},
        },
    })


@auth_customer
@require_POST
def payment_verify(request):
    order = _owned_order(request, request.POST.get('order_id', ''))
    payment_id = request.POST.get('razorpay_payment_id', '')
    signature = request.POST.get('razorpay_signature', '')
    returned_order_id = request.POST.get('razorpay_order_id', '')
    if not payment_id or not signature or returned_order_id != order.razorpay_order_id:
        return render(request, 'customer/payment_failed.html', {'order': order}, status=400)
    try:
        client = payments.get_client()
        client.utility.verify_payment_signature({
            'razorpay_order_id': order.razorpay_order_id,
            'razorpay_payment_id': payment_id, 'razorpay_signature': signature,
        })
    except razorpay.errors.SignatureVerificationError:
        logger.warning('Invalid checkout signature for local order %s', order.pk)
        return render(request, 'customer/payment_failed.html', {'order': order}, status=400)
    try:
        verified_payment = client.payment.fetch(payment_id)
    except Exception:
        # Gateway connectivity is uncertain; do not call a paid customer a failure.
        logger.exception('Cannot fetch payment for local order %s', order.pk)
        messages.info(request, 'We are still confirming payment. Please do not pay again.')
        return redirect('customer:payment_status', order_id=order.order_id)
    try:
        order = payments.record_captured_payment(order.razorpay_order_id, verified_payment)
    except payments.PaymentMismatch:
        logger.exception('Payment mismatch for local order %s', order.pk)
        return render(request, 'customer/payment_failed.html', {'order': order}, status=400)
    if not order.is_paid:
        return redirect('customer:payment_status', order_id=order.order_id)
    return _order_destination(order)


@auth_customer
def payment_status(request, order_id):
    payments.expire_reservations(request.session['customer'])
    order = _owned_order(request, order_id)
    if order.is_paid and order.payment_status != 'Review':
        return redirect('customer:order_success', order_id=order.order_id)
    return render(request, 'customer/payment_status.html', {'order': order})


@auth_customer
@require_POST
def check_payment(request, order_id):
    order = _owned_order(request, order_id)
    try:
        order = payments.reconcile_order(order)
    except (payments.PaymentMismatch, razorpay.errors.BadRequestError):
        logger.exception('Unable to match payment for local order %s', order.pk)
        messages.warning(request, 'We could not confirm this payment. Please contact support with your order number.')
    except Exception:
        logger.exception('Payment status lookup unavailable for local order %s', order.pk)
        messages.info(request, 'Payment status is temporarily unavailable. Do not pay again if money was deducted.')
    return _order_destination(order) if order.is_paid else redirect('customer:payment_status', order_id=order.order_id)


@auth_customer
@require_POST
def cancel_checkout(request, order_id):
    order = _owned_order(request, order_id)
    # Try to recover an already-captured payment before releasing the reservation.
    try:
        order = payments.reconcile_order(order)
    except Exception:
        logger.exception('Cannot check payment before cancelling order %s', order.pk)
        messages.warning(request, 'Payment status could not be checked. Please try again before starting another payment.')
        return redirect('customer:payment_status', order_id=order.order_id)
    if order.is_paid:
        return _order_destination(order)
    payments.release_checkout(order)
    messages.info(request, 'Checkout closed. Your cart has been kept. Any late payment will still be reconciled.')
    return redirect('customer:view_cart')


@csrf_exempt
@require_POST
def razorpay_webhook(request):
    secret = getattr(settings, 'RAZORPAY_WEBHOOK_SECRET', '')
    if not secret:
        return HttpResponse('Webhook is not configured.', status=503)
    try:
        # Use the exact raw body, not json.dumps() of the parsed payload.
        body = request.body.decode('utf-8')
        razorpay.Utility().verify_webhook_signature(
            body, request.headers.get('X-Razorpay-Signature', ''), secret,
        )
        event = json.loads(body)
    except (razorpay.errors.SignatureVerificationError, ValueError, UnicodeDecodeError):
        return HttpResponse('Invalid webhook.', status=400)
    if event.get('event') not in ['payment.captured', 'order.paid']:
        return HttpResponse('Ignored.')
    payment_data = event.get('payload', {}).get('payment', {}).get('entity', {})
    if not isinstance(payment_data, dict) or not payment_data.get('order_id'):
        return HttpResponse('Invalid payment event.', status=400)
    try:
        payments.record_captured_payment(payment_data['order_id'], payment_data)
    except Order.DoesNotExist:
        logger.error('Captured webhook has no linked local order; manual reconciliation required.')
        return HttpResponse('Order not linked yet.', status=503)
    except payments.PaymentMismatch:
        logger.exception('Webhook payment mismatch.')
        return HttpResponse('Payment mismatch.', status=400)
    return HttpResponse('OK')


def _display_order(order):
    items = list(order.items.select_related('product').order_by('pk'))
    order.purchased_items = items
    order.total_quantity = sum(item.quantity for item in items)
    order.books_subtotal = sum((item.line_total for item in items), Decimal('0.00'))
    return items


@auth_customer
def order_success(request, order_id):
    order = _owned_order(request, order_id)
    if not order.is_paid or order.payment_status == 'Review':
        return redirect('customer:payment_status', order_id=order.order_id)
    items = _display_order(order)
    return render(request, 'customer/order_success.html', {
        'order': order, 'order_items': items,
        'total_quantity': order.total_quantity, 'books_subtotal': order.books_subtotal,
    })


@auth_customer
def customer_myorders(request):
    orders = list(Order.objects.filter(
        customer_id=request.session['customer'], is_paid=True,
    ).order_by('-created_at', '-pk'))
    for order in orders:
        _display_order(order)
    pending_orders = Order.objects.filter(
        customer_id=request.session['customer'], is_paid=False,
    ).exclude(razorpay_order_id__isnull=True).exclude(razorpay_order_id='').order_by('-created_at')[:10]
    return render(request, 'customer/my orders.html', {
        'orders': orders, 'pending_orders': pending_orders,
    })
