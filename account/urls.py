from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .views import EsewaRequest, EsewaVerifyView

urlpatterns = [
    path('', views.index, name='index'),
    # for admin and ngo
    path('dashboard/', views.Dashboard.as_view(), name='dashboard'),
    path('ngos/', views.NGOListView.as_view(), name='list_ngo'),
    path('history/', views.HistoryListView.as_view(), name='list_history'),
    path('history/<int:pk>/delete', views.HistoryDeleteView.as_view(), name='delete_history'),
    path('ngo/<int:pk>/delete', views.NGODeleteView.as_view(), name='delete_ngo'),
    path('ngo/<int:pk>/details', views.NGODetailView.as_view(), name='detail_ngo'),
    path('donors/', views.DonorListView.as_view(), name='list_donor'),
    path('donor/<int:pk>/delete', views.DonorDeleteView.as_view(), name='delete_donor'),
    path('donor/<int:pk>/details', views.DonorDetailView.as_view(), name='detail_donor'),

    path('signup/', views.ngosignup, name='signup'),
    path('login/', views.login_home, name='login'),
    path('register/', views.register, name='register'),
    path('logout/', views.logoutUser, name='logout'),
    path('profile/', views.profile, name='profile'),
    path('ngoprofile/update', views.NGOProfileUpdateView.as_view(), name='update_ngo'),
    path('donorprofile/update', views.DonorProfileUpdateView.as_view(), name='update_donor'),
    path('ngorequest/<int:pk>/update', views.NGORequestUpdateView.as_view(), name='ngorequest_update'),
    path('donation/', views.DonationCreateView.as_view(), name='create_donation'),

    path('cause/create/', views.CreateCauseView.as_view(), name='create_cause'),
    path('cause/list/', views.CausesListView.as_view(), name='list_cause'),
    path('donation/list/', views.DonationListView.as_view(), name='list_donation'),
    path('cause/<int:pk>/delete', views.CausesDeleteView.as_view(), name='delete_cause'),
    path('cause/<int:pk>/edit', views.CauseUpdateView.as_view(), name='update_cause'),
    path('cause/<int:pk>', views.CausesDetailView.as_view(), name='detail_cause'),
    path('donation/<int:pk>', views.DonationDetailView.as_view(), name='detail_donation'),
    # for changin password after login
    path('password-change/', views.change_password, name='password_change'),
    # for resetting password
    path('reset_password/', auth_views.PasswordResetView.as_view(template_name="account/password_reset.html"),
         name="reset_password"),
    path('reset_password_sent/',
         auth_views.PasswordResetDoneView.as_view(template_name="account/password_reset_sent.html"),
         name="password_reset_done"),
    path('reset/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(template_name="account/password_reset_form.html"),
         name="password_reset_confirm"),
    path('reset_password_complete/',
         auth_views.PasswordResetCompleteView.as_view(template_name="account/password_reset_done.html"),
         name="password_reset_complete"),

    # for the esewa payment gateway
    path("esewa-request/", EsewaRequest.as_view(), name="esewarequest"),
    path("esewa-verify/", EsewaVerifyView.as_view(), name="esewaverify"),
]
