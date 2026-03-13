from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render,redirect
from random import randint
from .models import Customer
from .models import Seller
from django.core.mail import send_mail
from django.contrib import messages


def admin_login(request):
    return render(request, 'common/admin login.html')


def customer_login(request):
    # Security: If already logged in, redirect to catalog
    if 'customer' in request.session:
        return redirect('customer:cust_view_prod')

    if request.method == "POST":
        email = request.POST.get('email')
        password = request.POST.get('password')

        try:
            # 1. Authenticate against the Customer model
            customer = Customer.objects.get(c_email=email, c_password=password)
            
            # 2. Set Session (The Key for your @auth_customer decorator)
            request.session['customer'] = customer.id
            
            # 3. Success Feedback
            messages.success(request, f"Welcome back to the Archive, {customer.c_name}.")
            
            # 4. Redirect to Catalog
            return redirect('customer:cust_view_prod')

        except Customer.DoesNotExist:
            # 5. Professional Error Message (Don't reveal if it was the email or password)
            messages.error(request, "Invalid credentials. Access to the KitabHub archive denied.")
            return redirect('common:customer_login')

    return render(request, 'common/customerlogin.html')

def customer_register(request):
    if 'customer' in request.session:
        return redirect('customer:cust_view_prod')

    if request.method == "POST":
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        password = request.POST.get('password')

        # Check for existing account
        if Customer.objects.filter(c_email=email).exists():
            messages.error(request, "This email is already registered in the KitabHub archive.")
            return redirect('common:customer_register')

        try:
            # Create the record
            Customer.objects.create(
                c_name=name,
                c_email=email,
                c_phone=phone,
                c_password=password
            )
            print('success')
            
            # 1. Prepare the success message
            messages.success(request, "Registration Successful! Your KitabHub account is now active. Please Log In.")
            return redirect('common:customer_login')

        except Exception as e:
            messages.error(request, "An error occurred during archive initialization. Please try again.")
            return redirect('common:customer_register')

    return render(request, 'common/customer signup.html')


def project_home(request):
    return render(request, 'common/project home.html')


def seller_login(request):

    if request.method == "POST":
        email = request.POST.get('email')
        password = request.POST.get('password')

        try:
            seller = Seller.objects.get(s_email=email, s_password=password)
            
            # Check if verified by admin
            if not seller.is_verified:
                messages.warning(request, "Your account is pending verification by the KitabHub team.")
                return redirect('common:seller_login')

            request.session['seller'] = seller.id
            messages.success(request, f"Welcome, {seller.s_store_name} Archive Portal.")
            return redirect('seller:seller_home')

        except Seller.DoesNotExist:
            messages.error(request, "Invalid Seller credentials.")
            return redirect('common:seller_login')

    return render(request, 'common/seller login.html')


def seller_signup(request):
    if 'seller' in request.session:
        return redirect('seller:seller_dashboard') # Assuming you have a seller app dashboard

    if request.method == "POST":
        name = request.POST.get('name')
        email = request.POST.get('email')
        store_name = request.POST.get('store_name')
        phone = request.POST.get('phone')
        password = request.POST.get('password')

        # Check if seller already exists
        if Seller.objects.filter(s_email=email).exists():
            messages.error(request, "This email is already registered as a Seller.")
            return redirect('common:seller_signup')

        try:
            Seller.objects.create(
                s_name=name,
                s_email=email,
                s_store_name=store_name,
                s_phone=phone,
                s_password=password
            )
            messages.success(request, "Seller Registration Successful! Please wait for Admin verification.")
            return redirect('common:seller_login')
        except Exception as e:
            messages.error(request, "Error during registration. Please check your details.")
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

     
