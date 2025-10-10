from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.home_view, name='home'),  # root path
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path("update_user/", views.update_user, name="update_user"),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('chama/create/', views.create_chama, name='create_chama'),
    path('chama/<int:chama_id>/add-member/', views.add_member, name='add_member'),
    path('chama/<int:chama_id>/add-contribution/', views.add_contribution, name='add_contribution'),
    path('chama/<int:chama_id>/contributions/', views.contributions_list, name='contributions_list'),
    path('contributions/', views.contributions_overview, name='contributions_overview'),
    path("members/", views.members_home, name="members_home"),
    path("members/<int:chama_id>/", views.chama_members, name="chama_members"),
    path('accounts/', views.accounts_view, name='accounts'),
    #path("transactions/", views.transaction_list, name="transactions"),
    path('withdraw/<int:chama_id>/', views.withdraw_view, name='withdraw'),
    path("transactions/", views.transactions_view, name="transactions"),
    path('about/', views.about_view, name='about'),
    path('contact_support/', views.contact_support, name='contact_support'),




    # password reset
    path(
        'password-reset/',
        auth_views.PasswordResetView.as_view(template_name='app/password_reset.html'),
        name='password_reset'
    ),

    path(
        'password-reset/done',
        auth_views.PasswordResetView.as_view(template_name='app/password_reset_done.html'),
        name='password_reset_done'
    ),

    path(
        'reset/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(template_name='app/password_reset_confirm.html'),
        name='password_reset_confirm'
    ),

    path(
        'reset/done',
        auth_views.PasswordResetCompleteView.as_view(template_name='app/password_reset_complete.html'),
        name='password_reset_complete'
    ),
]