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
    path('productPage/<int:product_id>',views.productPage,name='productPage'),
    path('userProfile',views.userProfile,name='userProfile'),
    path('userAddress',views.userAddress,name='userAddress'),
    path('addAddress',views.addAddress,name='addAddress'),
    path('editAddress/<int:address_id>',views.editAddress,name='editAddress'),
    path('deleteAddress/<int:address_id>',views.deleteAddress,name='deleteAddress'),
    path('myCart',views.myCart,name='myCart'),
    path('addToCart/<int:product_id>',views.addToCart,name='addToCart'),
    path('removeFromCart/<int:product_id>',views.removeFromCart,name='removeFromCart'),
]