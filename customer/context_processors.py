from .models import Cart

def cart_count(request):
    # Initialize count at 0
    item_cnt = 0
    
    # Check if the customer is logged in via session
    if 'customer' in request.session:
        customer_id = request.session['customer']
        # Count the number of unique items in the cart for this customer
        item_cnt = Cart.objects.filter(customer_id=customer_id).count()
        
    return {
        'item_cnt': item_cnt
    }