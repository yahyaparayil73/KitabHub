from django.urls import path
from . import views
app_name = 'common'

urlpatterns = [
    path('comadminlogin', views.admin_login, name='admin_login'),
    path('customerlogin', views.customer_login, name='customer_login'),
    path('customersignup', views.customer_register, name='customer_register'),
    path('', views.project_home, name='project_home'),
    path('sellerlogin', views.seller_login, name='seller_login'),
    path('sellersignup', views.seller_signup, name='seller_signup'),
    path('mastercommon', views.master_common, name='master_common'),
    path('test', views.test, name='test'),
    path('email_exist', views.email_exist, name='email_exist'),
    path('salary_generator', views.salary_generator, name='salary_generator'),
    path('to_do_list', views.to_do_list, name='to_do_list'),



]
