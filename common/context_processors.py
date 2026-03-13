# # context_processors.py

# from common.models import Customer


# def customer_name(request):
#     customer_name = None
#     if 'customer' in request.session:
#         customer_id = request.session['customer']
#         try:
#             customer_name = Customer.objects.get(id=customer_id)
#         except Customer.DoesNotExist:
#             pass
#     return {'customer_nm': customer_name}
