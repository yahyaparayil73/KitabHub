from django.urls import path
from . import views
app_name='customer'
urlpatterns=[
    
    path('cchangepassword',views.customer_changepassword,name='changepassword'),
    path('product_details/<int:pid>/', views.product_details, name='product_details'),
    path('cprofile',views.customer_profile,name='customer_profile'),
    path('ccustomer_home/<int:cat_id>',views.customer_home_filter,name='home_filter'),
    path('ccustomer_home_a', views.customer_home, name='home'),
    path("search/", views.search_books, name="search_books"),
    path('cmyorders',views.customer_myorders,name='myorders'),
    path('c_logout',views.customer_logout,name='customer_logout'),
    path('master_customer',views.master_customer,name='master_customer'),
    path('cust_view_prod',views.cust_view_prod,name ='cust_view_prod'),
    path('view_cart/', views.view_cart, name='view_cart'),
    path('add-to-archive/<int:pid>/', views.add_to_cart, name='add_to_cart'),
    path('update-cart-qty/', views.update_cart_quantity, name='update_cart_quantity'),
    path('remove-from-cart/<int:cart_id>/', views.remove_from_cart, name='remove_from_cart'),

]