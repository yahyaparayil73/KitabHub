from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from common.models import Customer
from seller.models import Product
from customer.models import Cart
from django.shortcuts import get_object_or_404
from django.contrib.auth import logout
from django.db import transaction
import datetime  
from seller.decorators import auth_customer
from django.db.models import Q
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
def customer_mycart(request):  
    # customer = request.session['customer']
    # if not customer:
    #         return redirect('customer:login')
    # cust = Cart.objects.get(customer_id = customer)
    # cust_id = cust.id
    # cart_itms = Cart_items.objects.filter(Cart_id = cust_id)
    return render(request, 'customer/my cart.html')

@auth_customer
def update_quantity(request):
    msg = ''
    if request.method == 'POST':
        customer = request.session['customer']
        if not customer:
            return redirect('customer:login')
        cust = Cart.objects.get(customer_id = customer)
        cust_id = cust.id
        item_id = request.POST.get('product_id') 
        qty = int(request.POST.get('quantity'))                                                 #User entered quantity
        price = int(request.POST.get('amount'))  
        sub_total = price * qty  
        cart_itm = Cart_items.objects.get(product_id=item_id,Cart_id =cust_id)                  #Get cart item
        cart_itm.quantity = qty
        cart_itm.sub_total = sub_total
        cart_itm.save()                                                                         #update the cart quantity
        itm = Product.objects.get(id = item_id)
        qnty = itm.p_stock
        if qty > qnty: 
            msg = 'Out of Stock'
        else:
            msg = 'In Stock'
        return JsonResponse({'status': 'ok', 'message': msg})

def delete_item(request):
    if request.method == 'POST':
        customer = request.session['customer']
        if not customer:
            return redirect('customer:login')
        cust = Cart.objects.get(customer_id = customer)
        cust_id = cust.id
        product_id = request.POST.get('product_id')
        cart_item = Cart_items.objects.filter(product_id=product_id,Cart_id =cust_id)
        # print(cart_item.)
        cart_item.delete()
        return JsonResponse({'status': 'ok'})

@auth_customer
def customer_myorders(request):
    return render(request, 'customer/my orders.html')

@auth_customer
def product_details(request, pid):
    product = get_object_or_404(Product, id=pid)
    related_products = Product.objects.filter(p_genre=product.p_genre).exclude(id=pid)[:4]
    
    context = {
        'product': product,
        'related': related_products
    }
    # Changed space to underscore to match professional file naming
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
    # Get all products or filter by search query
    query = request.GET.get('q')
    if query:
        products = Product.objects.filter(
            Q(p_name__icontains=query) | Q(p_author__icontains=query) | Q(p_genre__icontains=query)
        ).order_by('-id')
    else:
        products = Product.objects.all().order_by('-id')

    customer_id = request.session.get('customer')
    customer = None
    if customer_id:
        customer = Customer.objects.get(id=customer_id)

    return render(request, 'customer/cust_view_prod.html', {
        'products': products,
        'customer': customer,
        'query': query
    })

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
