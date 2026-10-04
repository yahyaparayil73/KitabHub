from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render,redirect
from random import randint
from .models import Customer
from .models import Seller
from django.core.mail import send_mail
from django.contrib import messages
from django.contrib.auth.hashers import make_password
from django.db import migrations
from django.contrib.auth.hashers import check_password



def admin_login(request):
    return render(request, 'common/admin login.html')


def customer_login(request):
    if 'customer' in request.session:
        return redirect('customer:cust_view_prod')

    if request.method == "POST":
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')

        customer = Customer.objects.filter(c_email=email).first()

        if not customer or not check_password(
            password, customer.c_password
        ):
            messages.error(request, "Invalid email or password.")
            return redirect('common:customer_login')

        request.session.cycle_key()
        request.session['customer'] = customer.id

        messages.success(
            request,
            f"Welcome back to the Archive, {customer.c_name}.",
        )
        return redirect('customer:cust_view_prod')

    return render(request, 'common/customerlogin.html')

def customer_register(request):
    if 'customer' in request.session:
        return redirect('customer:cust_view_prod')

    if request.method == "POST":
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        password = request.POST.get('password')

        if not password:
            messages.error(request, "Please enter a password.")
            return redirect('common:customer_register')

        if Customer.objects.filter(c_email=email).exists():
            messages.error(request, "This email is already registered.")
            return redirect('common:customer_register')

        try:
            Customer.objects.create(
                c_name=name,
                c_email=email,
                c_phone=phone,
                c_password=make_password(password),
            )

            messages.success(
                request,
                "Registration successful! Please log in.",
            )
            return redirect('common:customer_login')

        except Exception:
            messages.error(
                request,
                "Registration failed. Please try again.",
            )
            return redirect('common:customer_register')

    return render(request, 'common/customer signup.html')

def project_home(request):
    return render(request, 'common/project home.html')


def seller_login(request):
    if 'seller' in request.session:
        return redirect('seller:seller_home')

    if request.method == "POST":
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')

        seller = Seller.objects.filter(s_email=email).first()

        if not seller or not check_password(password, seller.s_password):
            messages.error(request, "Invalid email or password.")
            return redirect('common:seller_login')

        if not seller.is_verified:
            messages.warning(
                request,
                "Your account is pending verification by the KitabHub team.",
            )
            return redirect('common:seller_login')

        request.session.cycle_key()
        request.session['seller'] = seller.id

        messages.success(
            request,
            f"Welcome, {seller.s_store_name} Archive Portal.",
        )
        return redirect('seller:seller_home')

    return render(request, 'common/seller login.html')

def seller_signup(request):
    if 'seller' in request.session:
        return redirect('seller:seller_home')

    if request.method == "POST":
        name = request.POST.get('name')
        email = request.POST.get('email', '').strip()
        store_name = request.POST.get('store_name')
        phone = request.POST.get('phone')
        password = request.POST.get('password')

        if not password:
            messages.error(request, "Please enter a password.")
            return redirect('common:seller_signup')

        if Seller.objects.filter(s_email=email).exists():
            messages.error(
                request,
                "This email is already registered as a seller.",
            )
            return redirect('common:seller_signup')

        try:
            Seller.objects.create(
                s_name=name,
                s_email=email,
                s_store_name=store_name,
                s_phone=phone,
                s_password=make_password(password),
            )

            messages.success(
                request,
                "Registration successful! Please wait for admin verification.",
            )
            return redirect('common:seller_login')

        except Exception:
            messages.error(
                request,
                "Registration failed. Please check your details.",
            )
            return redirect('common:seller_signup')

    return render(request, 'common/seller signup.html')

def master_common(request):
    return render(request, 'common/master_common.html')         

def test(request):
    return render(request, 'common/test.html')

def email_exist(request):
    email = request.POST.get('email_data', '')
    email_exists = Customer.objects.filter(c_email = email).exists()
    return JsonResponse({'email_exists':email_exists})

def salary_generator(request):
    return render(request, 'common/salary_generator.html')

def to_do_list(request):
    return render(request, 'common/to_do_list.html')

     
