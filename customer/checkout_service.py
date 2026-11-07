"""Payment and stock rules shared by the browser callback and Razorpay webhook.

All network calls stay outside database transactions. Customer -> Order is the
consistent lock order. Conditional stock updates also prevent negative stock.
"""
import logging
from datetime import timedelta
from decimal import Decimal

import razorpay
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import transaction
from django.db.models import F
from django.utils import timezone

from common.models import Customer
from seller.models import Product
from .models import Cart, Order, OrderItem

logger = logging.getLogger(__name__)


class CheckoutProblem(Exception):
    pass


class PaymentMismatch(Exception):
    pass


def get_client():
    key_id = settings.RAZORPAY_KEY_ID
    key_secret = settings.RAZORPAY_KEY_SECRET

    if not key_id or not key_secret:
        raise ImproperlyConfigured(
            "Configure the Razorpay key ID and secret in settings."
        )

    return razorpay.Client(auth=(key_id, key_secret))


def amount_paise(order):
    if order.total_amount is None or order.total_amount <= 0:
        raise CheckoutProblem('This order has an invalid total. Contact support.')
    value = order.total_amount * 100
    if value != value.to_integral_value():
        raise CheckoutProblem('Order prices must use two decimal places.')
    return int(value)


def _reserve(items):
    for item in sorted(items, key=lambda row: row.product_id or 0):
        if not item.product_id or item.quantity < 1:
            raise CheckoutProblem('A book in this order is no longer available.')
        changed = Product.objects.filter(
            pk=item.product_id, p_stock__gte=item.quantity,
        ).update(p_stock=F('p_stock') - item.quantity)
        if not changed:
            raise CheckoutProblem('There is not enough stock for one of these books.')


def _release(order):
    # Caller holds the customer and order locks inside transaction.atomic().
    if not order.stock_reserved:
        return
    for item in order.items.order_by('product_id', 'pk'):
        if item.product_id:
            Product.objects.filter(pk=item.product_id).update(
                p_stock=F('p_stock') + item.quantity,
            )
    order.stock_reserved = False


def expire_reservations(customer_id=None, limit=100):
    candidates = Order.objects.filter(
        stock_reserved=True, is_paid=False,
        payment_status__in=['Initializing', 'Pending'],
        reservation_expires_at__lte=timezone.now(),
    )
    if customer_id is not None:
        candidates = candidates.filter(customer_id=customer_id)
    released = 0
    for pk, owner in list(candidates.values_list('pk', 'customer_id')[:limit]):
        with transaction.atomic():
            Customer.objects.select_for_update().get(pk=owner)
            order = Order.objects.select_for_update().get(pk=pk)
            if (order.stock_reserved and not order.is_paid
                    and order.payment_status in ['Initializing', 'Pending']
                    and order.reservation_expires_at <= timezone.now()):
                _release(order)
                order.payment_status = 'Expired'
                order.save(update_fields=['stock_reserved', 'payment_status'])
                released += 1
    return released


def create_checkout(customer_id, data):
    """Freeze books/prices, reserve stock and create exactly one local attempt."""
    expire_reservations(customer_id)
    with transaction.atomic():
        Customer.objects.select_for_update().get(pk=customer_id)
        existing = Order.objects.filter(
            customer_id=customer_id, checkout_token=data['checkout_token'],
        ).first()
        if existing:
            return existing, False
        active = Order.objects.filter(
            customer_id=customer_id,
            payment_status__in=['Initializing', 'Pending'],
            reservation_expires_at__gt=timezone.now(),
        ).first()
        if active:
            return active, False

        rows = list(Cart.objects.filter(customer_id=customer_id).select_related('product').order_by('pk'))
        if not rows:
            raise CheckoutProblem('Your cart is empty.')
        total = Decimal('0.00')
        for row in rows:
            price = Decimal(str(row.product.p_price))
            if (not price.is_finite() or price <= 0
                    or price != price.quantize(Decimal('0.01')) or row.quantity < 1):
                raise CheckoutProblem('A cart item has an invalid price or quantity.')
            total += price * row.quantity
        if total > Decimal('99999999.99'):
            raise CheckoutProblem('This order exceeds the supported total.')

        order = Order.objects.create(
            customer_id=customer_id, checkout_token=data['checkout_token'],
            full_name=data['full_name'], email=data['email'], shipping_address=data['address'],
            total_amount=total, status='Pending', is_paid=False,
            payment_status='Initializing', stock_reserved=True,
            reservation_expires_at=timezone.now() + timedelta(
                minutes=getattr(settings, 'CHECKOUT_RESERVATION_MINUTES', 15),
            ),
        )
        for row in rows:
            OrderItem.objects.create(
                order=order, product=row.product, quantity=row.quantity,
                price_at_purchase=row.product.p_price,
                product_name=row.product.p_name,
                product_author=str(getattr(row.product, 'p_author', '') or ''),
                source_cart_id=row.pk, source_cart_updated_at=row.updated_at,
            )
        _reserve(list(order.items.all()))
        return order, True


def initialize_gateway(order):
    """Called only for a newly created attempt; repeated posts reuse that attempt."""
    try:
        remote = get_client().order.create({
            'amount': amount_paise(order), 'currency': 'INR', 'receipt': order.order_id,
        })
        gateway_id = remote['id']
    except Exception:
        # This catch is ONLY around gateway initialization. No customer payment
        # has been submitted yet, and verification errors are not swallowed here.
        logger.exception('Unable to initialize gateway order for local order %s', order.pk)
        with transaction.atomic():
            Customer.objects.select_for_update().get(pk=order.customer_id)
            locked = Order.objects.select_for_update().get(pk=order.pk)
            if locked.payment_status == 'Initializing':
                _release(locked)
                locked.payment_status = 'Failed'
                locked.save(update_fields=['stock_reserved', 'payment_status'])
        order.refresh_from_db()
        return order

    with transaction.atomic():
        Customer.objects.select_for_update().get(pk=order.customer_id)
        locked = Order.objects.select_for_update().get(pk=order.pk)
        locked.razorpay_order_id = gateway_id
        if locked.payment_status == 'Initializing':
            locked.payment_status = 'Pending'
        locked.save(update_fields=['razorpay_order_id', 'payment_status'])
    order.refresh_from_db()
    return order


def record_captured_payment(gateway_order_id, payment):
    """Idempotent finalization. Payment comes from an API fetch or signed webhook."""
    candidate = Order.objects.get(razorpay_order_id=gateway_order_id)
    if (payment.get('order_id') != gateway_order_id
            or payment.get('amount') != amount_paise(candidate)
            or payment.get('currency') != 'INR' or not payment.get('id')):
        raise PaymentMismatch('The payment does not match the saved order.')
    if payment.get('status') != 'captured':
        return candidate

    with transaction.atomic():
        Customer.objects.select_for_update().get(pk=candidate.customer_id)
        order = Order.objects.select_for_update().get(pk=candidate.pk)
        if order.is_paid:
            if order.razorpay_payment_id != payment['id']:
                raise PaymentMismatch('A different payment is already attached to this order.')
            return order

        items = list(order.items.order_by('product_id', 'pk'))
        reason = ''
        if not order.checkout_token or not items:
            reason = 'Legacy checkout or missing order items: reconcile manually.'
        elif sum((item.line_total for item in items), Decimal('0.00')) != order.total_amount:
            reason = 'Saved item prices do not match the saved order total.'
        elif any(item.product_id is None for item in items):
            reason = 'A purchased product was deleted before payment confirmation.'
        elif not order.stock_reserved:
            # Late capture after expiration: try to allocate again. A savepoint
            # makes allocation all-or-nothing even if one product is unavailable.
            try:
                with transaction.atomic():
                    _reserve(items)
            except CheckoutProblem:
                reason = 'Payment arrived after stock was released; stock unavailable.'

        if reason:
            _release(order)
            order.payment_status = 'Review'
            order.review_reason = reason
            logger.error('Paid order %s needs manual review: %s', order.pk, reason)
        else:
            # Reserved stock was already deducted at checkout. Do not deduct again.
            order.stock_reserved = False
            order.payment_status = 'Paid'
            for item in items:
                # Never delete newly added rows or rows edited after checkout.
                Cart.objects.filter(
                    pk=item.source_cart_id, customer_id=order.customer_id,
                    product_id=item.product_id, quantity=item.quantity,
                    updated_at=item.source_cart_updated_at,
                ).delete()

        order.is_paid = True
        order.razorpay_payment_id = payment['id']
        order.save(update_fields=[
            'is_paid', 'razorpay_payment_id', 'payment_status',
            'stock_reserved', 'review_reason',
        ])
        return order


def reconcile_order(order):
    if order.is_paid or not order.razorpay_order_id:
        return order
    result = get_client().order.payments(order.razorpay_order_id)
    for payment in result.get('items', []):
        if payment.get('status') == 'captured':
            return record_captured_payment(order.razorpay_order_id, payment)
    order.refresh_from_db()
    return order


def release_checkout(order):
    """Cancel an unpaid local reservation. A late capture still goes through review/allocation."""
    with transaction.atomic():
        Customer.objects.select_for_update().get(pk=order.customer_id)
        locked = Order.objects.select_for_update().get(pk=order.pk)
        if not locked.is_paid and locked.payment_status in ['Pending', 'Initializing']:
            _release(locked)
            locked.payment_status = 'Expired'
            locked.save(update_fields=['stock_reserved', 'payment_status'])
    return locked
