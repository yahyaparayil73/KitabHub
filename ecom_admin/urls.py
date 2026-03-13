from django.urls import path
from .import views
app_name='ecom_admin'


urlpatterns = [
    path('approve sellers',views.approve_sellers,name='approve sellers'),
    path('ecom_home',views.ecom_home,name='ecom_home'),
    path('view_order',views.view_order,name='view_order'),
    path('view_product',views.view_product,name='view_product'),
    path('view_seller', views.view_seller, name='view_seller'),
    path('sellers/remove/<int:seller_id>/', views.remove_seller, name='remove_seller'),
    path('view_customer', views.view_customer, name='view_customer'),
    path('customers/remove/<int:customer_id>/', views.remove_customer, name='remove_customer'),
    # path('remove_product',views.remove_product,name='remove_product'),
    path('admin_master',views.admin_master,name='admin_master'),

    

]