# from .models import Cart, Cart_items

# def cart_item_count(request):

#     customer_id = request.session['customer']
#     cart = Cart.objects.get(customer_id=customer_id)
#     cart_items = Cart_items.objects.filter(Cart_id=cart.id)
#     cnt = cart_items.count()
#     return {'item_cnt': cnt}