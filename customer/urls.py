from django.urls import path
from . import views
app_name='customer'
urlpatterns=[
    
    path('cmycart',views.customer_mycart,name='mycart'),
    path('cchangepassword',views.customer_changepassword,name='changepassword'),
    path('product_details/<int:pid>/', views.product_details, name='product_details'),
    path('cprofile',views.customer_profile,name='customer_profile'),
    path('ccustomer_home/<int:cat_id>',views.customer_home_filter,name='home_filter'),
    path('ccustomer_home_a', views.customer_home, name='home'),
    path("search/", views.search_books, name="search_books"),
    path('cmyorders',views.customer_myorders,name='myorders'),
    path('c_logout',views.customer_logout,name='customer_logout'),
    path('master_customer',views.master_customer,name='master_customer'),
    path('update_quantity',views.update_quantity,name ='update_quantity'),
    path('cust_view_prod',views.cust_view_prod,name ='cust_view_prod'),
    path('delete_item', views.delete_item, name='delete_item')

]