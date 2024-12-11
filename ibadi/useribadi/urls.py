from django.urls import path
from . import views
from .views import userSignup

urlpatterns = [
    path('',views.index,name='index'),
    path('userSignup',views.userSignup,name='userSignup'),
    path('signupOtp',views.signupOtp,name='signupOtp'),
    path('userLogin',views.userLogin,name='userLogin'),
    path('userHome',views.userHome,name='userHome'),
    path('userLogout',views.userLogout,name='userLogout'),
    path('resendOtp',views.resendOtp,name='resendOtp'),
    path('shop',views.shop,name='shop'),
    path('productPage/<int:product_id>',views.productPage,name='productPage')
]
