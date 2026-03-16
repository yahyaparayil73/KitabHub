from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from common.models import Customer
from seller.models import Product
from customer.models import Cart
from django.shortcuts import get_object_or_404
from django.contrib.auth import logout
from django.db import transaction
from django.contrib import messages
import datetime  
from seller.decorators import auth_customer
from django.db.models import Q
from django.template.loader import render_to_string
from django.db import connection
import time
import os     

@auth_customer
def customer_home(request):
    # 1. Fetch only Best Sellers
    new_arrivals = Product.objects.filter(best_seller='Yes').order_by('-id')
    
    # 2. Session Security Check
    customer_id = request.session.get('customer')
    if not customer_id:
        return redirect('customer:login')
    
    # 3. Secure Customer Retrieval
    try:
        customer = Customer.objects.get(id=customer_id)
        cust_nm = customer.c_name
    except Customer.DoesNotExist:
        # If session is invalid, clear it and redirect
        request.session.flush()
        return redirect('customer:login')

    context = {
        'new_arrvl': new_arrivals,
        'name': cust_nm
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
def add_to_cart(request, pid):
    
    customer_id = request.session['customer']
    product = get_object_or_404(Product, id=pid)
    exists = Cart.objects.filter(customer_id=customer_id, product_id=pid).exists()
    
    if exists:
        messages.info(request, "This volume is already in your selection.")
        return redirect('customer:view_cart') # Go straight to cart if already there
    
    Cart.objects.create(customer_id=customer_id, product_id=pid, quantity=1)
    messages.success(request, "Archive updated: Volume added to selections.")
    return redirect('customer:view_cart')

@auth_customer
def view_cart(request):
    
    cart_items = Cart.objects.filter(customer_id=request.session['customer'])
    grand_total = sum(item.total_price for item in cart_items)
    
    return render(request, 'customer/my cart.html', {
        'cart_items': cart_items,
        'grand_total': grand_total
    })

@auth_customer
def update_cart_quantity(request):
    # This handles the AJAX real-time updates
    cart_id = request.GET.get('cart_id')
    action = request.GET.get('action')
    item = get_object_or_404(Cart, id=cart_id)
    
    if action == 'plus':
        item.quantity += 1
    elif action == 'minus' and item.quantity > 1:
        item.quantity -= 1
    
    item.save()
    return JsonResponse({
        'status': 'success',
        'qty': item.quantity,
        'item_total': item.total_price,
        'grand_total': sum(i.total_price for i in Cart.objects.filter(customer=item.customer))
    })

def remove_from_cart(request, cart_id):
    # Security: Ensure the item belongs to the logged-in customer
    if 'customer' not in request.session:
        return redirect('common:customer_login')
        
    item = get_object_or_404(Cart, id=cart_id, customer_id=request.session['customer'])
    product_name = item.product.p_name # Store name for the success message
    item.delete()
    
    messages.success(request, f"'{product_name}' has been removed from your archive.")
    return redirect('customer:view_cart')


@auth_customer
def customer_myorders(request):
    return render(request, 'customer/my orders.html')

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
    
    # Recommended: ensure your filename is product_details.html (with underscore)
    return render(request, 'customer/product details.html', context)

@auth_customer
def customer_changepassword(request):
    msg = ''
    if request.method == "POST":
        oldpassword = request.POST['old_password']
        newpassword = request.POST['new_password']
        customer = Customer.objects.get(id=request.session['customer'])
        if customer.c_password == oldpassword:
            customer.c_password = newpassword
            customer.save()
            msg = 'Password Updated'
        else:
            msg = 'Passwords does not match'        

    return render(request, 'customer/change password.html', {'message': msg})

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
    print(customer)
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
