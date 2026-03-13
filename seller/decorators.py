

from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps

def auth_seller(func):
    @wraps(func) # This preserves the original function's name and metadata
    def wrapper(request, *args, **kwargs):
        if 'seller' not in request.session:
            # Professional warning message
            messages.warning(request, "Access Denied. Please authenticate as a Seller to continue.")
            return redirect('common:seller_login')
        
        # CRITICAL: You must CALL the function, not just return it
        return func(request, *args, **kwargs)
    
    return wrapper

def auth_customer(func):
    @wraps(func)
    def wrapper(request, *args, **kwargs):
        # Check if the customer key exists in the session
        if 'customer' not in request.session:
            messages.warning(request, "Secure Session Required. Please login to access your collection.")
            
            # Redirect to your specific customer login page
            # Assuming your namespace is 'customer' and name is 'login'
            return redirect('common:customer_login')
        
        # If they are logged in, execute the view function
        return func(request, *args, **kwargs)
    
    return wrapper