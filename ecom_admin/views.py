from common.models import Customer, Seller
from seller.models import Product
from django.shortcuts import render, redirect, get_object_or_404


def approve_sellers(request):
    return render(request, 'ecom_admin/approve sellers.html')


def ecom_home(request):
    return render(request, 'ecom_admin/home.html')

# 2. Seller Logic
def view_seller(request):
    sellers = Seller.objects.all().order_by('-id')
    return render(request, 'ecom_admin/view_seller.html', {'sellers': sellers})

def remove_seller(request, seller_id):
    get_object_or_404(Seller, id=seller_id).delete()
    return redirect('ecom_admin:remove_customer')

# 3. Customer Logic
def view_customer(request):
    customers = Customer.objects.all().order_by('-id')
    return render(request, 'ecom_admin/view_customer.html', {'customers': customers})

def remove_customer(request, customer_id):
    get_object_or_404(Customer, id=customer_id).delete()
    return redirect('ecom_admin:remove_customer')


def view_order(request):
    # Fetching all orders, latest first
    orders = Order.objects.all().order_by('-id')
    return render(request, 'ecom_admin/view_order.html', {'orders': orders})


def view_product(request):
    # Fetching products with seller info (using select_related to optimize database hits)
    products = Product.objects.all()    
    return render(request, 'ecom_admin/view_product.html', {'products': products})


def admin_master(request):
    return render(request, 'ecom_admin/admin_master.html')
