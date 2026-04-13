from django.contrib import admin
from django.urls import path
from core import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('doctors/', views.doctors_list, name='doctors'),
    path('doctors/<int:doctor_id>/', views.doctor_detail, name='doctor_detail'),
    path('book/', views.book_appointment, name='book_appointment'),
path('appointments/', views.my_appointments, name='my_appointments'),
path('appointments/cancel/<int:apt_id>/', views.cancel_appointment, name='cancel_appointment'),
path('ai-symptom-check/', views.ai_symptom_check, name='ai_symptom_check'),
path('chatbot/', views.chatbot_page, name='chatbot'),
path('chatbot/message/', views.chatbot_message, name='chatbot_message'),
path('create-payment/', views.create_payment, name='create_payment'),
path('payment-success/', views.payment_success, name='payment_success'),
path('quiz/', views.quiz_page, name='quiz'),
path('quiz/question/', views.get_quiz_question, name='get_quiz_question'),
path('lock-slot/', views.lock_slot, name='lock_slot'),
path('doctor-dashboard/', views.doctor_dashboard, name='doctor_dashboard'),
path('appointments/complete/<int:apt_id>/', views.mark_complete, name='mark_complete'),
path('appointments/reschedule/<int:apt_id>/', views.reschedule_appointment, name='reschedule_appointment'),
path('doctor/add-slot/', views.add_slot, name='add_slot'),
path('doctor/delete-slot/<int:slot_id>/', views.delete_slot, name='delete_slot'),
]