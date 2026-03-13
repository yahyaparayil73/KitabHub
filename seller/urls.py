from django.urls import path
from . import views
app_name='seller'


urlpatterns=[
    path('addproduct',views.add_product,name='add_product'),
    path('changepassword',views.change_password,name='changepassword'),
    path('sellerhome',views.seller_home,name='seller_home'),
    path('productcatalogue',views.product_catalogue),
    path('sellerprofile',views.seller_profile,name='seller_profile'),
    path('updatestock',views.update_stock,name='update_stock'),
    path('vieworders',views.view_orders,name='view_orders'),
    path('master_seller',views.master_seller,name='master_seller'),
    path('view_product',views.view_product,name='view_product'),
    path('s_logout',views.seller_logout,name='logout'),
    path('stock_update',views.stock_update,name='stock_update'),



]