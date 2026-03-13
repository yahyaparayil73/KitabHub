from django.shortcuts import redirect, render
from common.models import Seller
from seller.decorators import auth_seller
from seller.models import Product
from django.http import JsonResponse

# @auth_seller
# def add_product(request):
#     msg = ''
#     if request.method == 'POST':
#         pname = request.POST['p_name']
#         pdescription = request.POST['p_description']
#         pauthor = request.POST['p_author']
#         pnumber = request.POST['p_number']
#         pstock = request.POST['p_current_stock']
#         pgenre = request.POST['p_genre']
#         pprice = request.POST['p_price']
#         pimage = request.FILES['p_image']        
#         new_product = Product(
#             p_name=pname,
#             p_description=pdescription,
#             p_author = pauthor,
#             p_number= pnumber,
#             p_stock=pstock,
#             p_price=pprice,
#             p_genre = pgenre,
#             p_image=pimage,
#             seller_id=request.session['seller']
#         )

#         new_product.save()

#     return render(request, 'seller/add product.html', {'success_message': msg})

@auth_seller
def add_product(request):
    if request.method == 'POST':
        # Fetch the seller instance from the session
        seller_id = request.session.get('seller')
        seller_instance = Seller.objects.get(id=seller_id)
        
        # Get data from POST
        p_name = request.POST.get('p_name')
        p_description = request.POST.get('p_description')
        p_author = request.POST.get('p_author')
        p_number = request.POST.get('p_number') # New: ISBN or Reference Number
        p_stock = request.POST.get('p_stock')
        p_price = request.POST.get('p_price')
        p_genre = request.POST.get('p_genre')
        p_year = request.POST.get('p_year')
        best_seller = request.POST.get('best_seller') # New
        p_image = request.FILES.get('p_image')

        # Save to Model
        Product.objects.create(
            seller=seller_instance,
            p_name=p_name,
            p_description=p_description,
            p_author=p_author,
            p_number=p_number,
            p_stock=p_stock,
            p_price=p_price,
            p_genre=p_genre,
            p_year=p_year,
            best_seller=best_seller,
            p_image=p_image
        )
        
        return render(request, 'seller/add product.html', {'success_message': 'Volume Authorized Successfully'})

    return render(request, 'seller/add product.html')


# @auth_seller
def change_password(request):
    if request.method == "POST":
        exstng_pwd = request.POST.get("exisitng_password")
        newpassword = request.POST.get("new_password")
        confirmpassword = request.POST.get("confirm_password")

        try:
            seller = Seller.objects.get(id=request.session["seller"])
        except Seller.DoesNotExist:
            return JsonResponse({"error": "Seller not found"}, status=404)

        if seller.s_password == exstng_pwd:
            if newpassword == confirmpassword:
                seller.s_password = newpassword
                seller.save()
                return JsonResponse({"success": "Password updated successfully"})
            else:
                return JsonResponse({"error": "Passwords not match"}, status=400)
        else:
            return JsonResponse({"error": "The password "}, status=400)

    return JsonResponse({"error": "Invalid request"}, status=400)

@auth_seller
def seller_home(request):
    seller_data = Seller.objects.get(id=request.session['seller'])
    return render(request, 'seller/seller home.html', {'seller_data': seller_data})


def product_catalogue(request):
    return render(request, 'seller/product catalogue.html')


@auth_seller
def seller_profile(request):

    # Fetch seller data
    seller_data = Seller.objects.get(id=request.session['seller'])

    return render(request, 'seller/seller profile.html', {
        'seller': seller_data
    })

# @auth_seller
def update_stock(request):
    print('hiiii')
    products = Product.objects.filter(
        seller=request.session['seller']).values('id', 'p_name')
    if request.method == 'POST':
        prodnum = request.POST['p_number']
        new_stock = request.POST['new_stock']
        product1 = Product.objects.get(id=prodnum)
        product1.p_stock += int(new_stock)
        product1.save() 

    return render(request, 'seller/update stock.html', {'products': products})

@auth_seller
def view_product(request):
    selr_id = request.session['seller']                                                            
    product = Product.objects.filter(seller_id = selr_id)
    return render(request, 'seller/view_product.html', {'products': product})

@auth_seller
def view_orders(request):
    return render(request, 'seller/view orders.html')

@auth_seller
def master_seller(request):
    return render(request, 'seller/master_seller.html')

def seller_logout(request):
    del request.session['seller']
    request.session.flush()
    return redirect('common:seller_login')

def stock_update(request):
    product_id = request.POST['product_id']
    product = Product.objects.filter(id=product_id).values('p_stock')
    current_stock = product[0]['p_stock']
    return JsonResponse({'stock': current_stock})
