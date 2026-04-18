from urllib import request

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from .models import Patient
from .forms import RegisterForm
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
from .models import Patient, Doctor, Specialization, Slot, Appointment, UserProfile


def home(request):
    specializations = Specialization.objects.all()
    features = [
        {'icon':'👨‍⚕️', 'title':'Verified Doctors',
         'desc':'All doctors verified and credentialed'},
        {'icon':'⚡', 'title':'Instant Booking',
         'desc':'Book appointments in under 2 minutes'},
        {'icon':'🤖', 'title':'AI Guidance',
         'desc':'24/7 AI health assistant support'},
        {'icon':'🔒', 'title':'Secure Payments',
         'desc':'100% secure Razorpay payments'},
    ]
    return render(request, 'home.html', {
        'specializations': specializations,
        'features': features,
    })
def register_view(request):
    form = RegisterForm()

    if request.method == 'POST':
        form = RegisterForm(request.POST)

        if form.is_valid():
            email = form.cleaned_data['email'].lower().strip()

            # get role from form
            role = form.cleaned_data.get('role')

            # create user (ONLY ONCE)
            user = User.objects.create_user(
                username=email,
                email=email,
                password=form.cleaned_data['password'],
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name'],
            )

            # update profile (created by signal)
            profile = user.userprofile
            profile.role = role
            profile.save()

            # doctor linking (optional)
            if role == 'doctor':
                detected_doctor = Doctor.objects.filter(
                    name__iexact=user.first_name
                ).first()

                if detected_doctor:
                    detected_doctor.user = user
                    detected_doctor.save()

                messages.success(request, f'Welcome Doctor! Login now.')

            else:
                Patient.objects.get_or_create(
                    user=user,
                    defaults={
                        'phone': form.cleaned_data.get('phone', '0000000000'),
                        'age': form.cleaned_data.get('age', 0),
                        'gender': form.cleaned_data.get('gender', 'Other'),
                    }
                )

                messages.success(request, 'Account created! Please login.')

            return redirect('login')

    return render(request, 'register.html', {'form': form})

    return render(request, 'register.html', {'form': form})
from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from django.contrib import messages

def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect("home")
        else:
            messages.error(request, "Invalid username or password")

    return render(request, "login.html")

def logout_view(request):
    logout(request)
    return redirect('home')

from .models import Patient, Doctor, Specialization

def doctors_list(request):
    doctors = Doctor.objects.filter(available=True)
    specializations = Specialization.objects.all()
    
    spec = request.GET.get('spec', '')
    search = request.GET.get('search', '')
    
    if spec:
        doctors = doctors.filter(specialization__name=spec)
    
    if search:
        from django.db.models import Q
        doctors = doctors.filter(
            Q(name__icontains=search) | 
            Q(specialization__name__icontains=search)
        )
    
    return render(request, 'doctors.html', {
        'doctors': doctors,
        'specializations': specializations,
        'selected_spec': spec,
        'search': search,
    })
def doctor_detail(request, doctor_id):
    doctor = Doctor.objects.get(id=doctor_id)
    return render(request, 'doctor_detail.html', {'doctor': doctor})

from django.contrib.auth.decorators import login_required
from .models import Patient, Doctor, Specialization, Slot, Appointment
import json
from django.http import JsonResponse

def doctor_detail(request, doctor_id):
    doctor = Doctor.objects.get(id=doctor_id)
    # Get available slots grouped by date
    from datetime import date
    slots = Slot.objects.filter(
        doctor=doctor,
        is_booked=False,
        date__gte=date.today()
    ).order_by('date', 'time')
    
    # Group slots by date
    slots_by_date = {}
    for slot in slots:
        date_key = slot.date.strftime('%A, %d %B %Y')
        if date_key not in slots_by_date:
            slots_by_date[date_key] = []
        slots_by_date[date_key].append(slot)
    
    return render(request, 'doctor_detail.html', {
        'doctor': doctor,
        'slots_by_date': slots_by_date,
    })

@login_required
def book_appointment(request):
    if request.method == 'POST':
        slot_id = request.POST.get('slot_id')
        notes = request.POST.get('notes', '')
        
        try:
            slot = Slot.objects.get(id=slot_id, is_booked=False)
            
            # Fix: get or create patient automatically
            patient, created = Patient.objects.get_or_create(
                user=request.user,
                defaults={
                    'phone': '0000000000',
                    'age': 0,
                    'gender': 'Other'
                }
            )
            
            # Check already booked
            if Appointment.objects.filter(slot=slot).exists():
                messages.error(request, 'Slot already taken! Please choose another.')
                return redirect(f'/doctors/{slot.doctor.id}/')
            
            Appointment.objects.create(
                patient=patient,
                slot=slot,
                notes=notes,
            )
            slot.is_booked = True
            slot.save()
            
            messages.success(request, 
                f'✅ Appointment booked with Dr. {slot.doctor.name} on {slot.date} at {slot.time.strftime("%I:%M %p")}!')
            return redirect('my_appointments')
        
        except Slot.DoesNotExist:
            messages.error(request, 'Slot not found!')
            return redirect('doctors')
        except Exception as e:
            messages.error(request, f'Booking failed! {str(e)}')
            return redirect('doctors')
    
    return redirect('doctors')
from datetime import date
@login_required
def my_appointments(request):
    try:
        patient = Patient.objects.get(user=request.user)
        appointments = Appointment.objects.filter(
            patient=patient
        ).order_by('-created_at')
    except:
        appointments = []
    
    return render(request, 'my_appointments.html', {
        'appointments': appointments,
        'today': date.today(),
    })

@login_required  
def cancel_appointment(request, apt_id):
    try:
        patient = Patient.objects.get_or_create(
            user=request.user,
            defaults={'phone':'0000000000','age':0,'gender':'Other'}
        )[0]
        apt = Appointment.objects.get(id=apt_id, patient=patient)
        
        # Free up the slot
        apt.slot.is_booked = False
        apt.slot.save()
        
        # DELETE completely from DB
        apt.delete()
        
        messages.success(request, 'Appointment cancelled successfully.')
    except Exception as e:
        messages.error(request, f'Could not cancel! {str(e)}')
    return redirect('my_appointments')

from groq import Groq
from django.conf import settings
from django.http import JsonResponse
import json

def ai_symptom_check(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            symptoms = data.get('symptoms', '')

            if not symptoms.strip():
                return JsonResponse({
                    'suggestion': 'Please describe your symptoms first!'
                })

            client = Groq(api_key=settings.GROQ_API_KEY)

            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",  # ✅ FIXED
                messages=[
                    {
                        "role": "system",
                        "content": """You are a helpful medical assistant. 
                        When user describes symptoms, suggest which type 
                        of doctor specialist they should consult.
                        Keep response short, clear and friendly.
                        Always end with: 'Please consult a real doctor for proper diagnosis.'"""
                    },
                    {
                        "role": "user", 
                        "content": f"My symptoms are: {symptoms}"
                    }
                ],
                temperature=0.7,
                max_tokens=300
            )

            suggestion = response.choices[0].message.content

            return JsonResponse({
                'suggestion': suggestion,
                'status': 'success'
            })

        except Exception as e:
            return JsonResponse({
                'suggestion': f'AI Error: {str(e)}',
                'status': 'error'
            })

    return JsonResponse({'error': 'POST method only'})

def chatbot_page(request):
    return render(request, 'chatbot.html')

def chatbot_message(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_message = data.get('message', '')
            # history = list of {role, content}
            history = data.get('history', [])
            
            if not user_message.strip():
                return JsonResponse({'reply': 'Please type something!'})
            
            client = Groq(api_key=settings.GROQ_API_KEY)
            
            # Build messages list with full history
            messages_list = [
                {
                    "role": "system",
                    "content": """You are DocPro's friendly AI medical assistant. 
Help patients understand their symptoms and suggest which specialist to consult.
Ask follow-up questions to understand better.
Be conversational, warm and helpful.
Always remind: consult a real doctor for proper diagnosis.
Keep responses concise and clear."""
                }
            ]
            
            # Add conversation history
            for msg in history:
                messages_list.append({
                    "role": msg['role'],
                    "content": msg['content']
                })
            
            # Add current message
            messages_list.append({
                "role": "user",
                "content": user_message
            })
            
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages_list,
                temperature=0.7,
                max_tokens=400
            )
            
            reply = response.choices[0].message.content
            
            return JsonResponse({
                'reply': reply,
                'status': 'success'
            })
        
        except Exception as e:
            return JsonResponse({
                'reply': f'Sorry, I am unavailable right now. Error: {str(e)}',
                'status': 'error'
            })
    
    return JsonResponse({'error': 'POST only'})

import razorpay
from django.views.decorators.csrf import csrf_exempt

# Create Razorpay order when slot selected
@login_required
def create_payment(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            slot_id = data.get('slot_id')
            notes = data.get('notes', '')
            
            slot = Slot.objects.get(id=slot_id, is_booked=False)
            doctor = slot.doctor
            
            # Amount in paise (₹1 = 100 paise)
            # Using ₹1 for demo (100 paise)
            amount = doctor.fee * 100
            
            client = razorpay.Client(
                auth=(settings.RAZORPAY_KEY_ID, 
                      settings.RAZORPAY_KEY_SECRET)
            )
            
            # Create order
            order = client.order.create({
                'amount': amount,
                'currency': 'INR',
                'payment_capture': 1,
                'notes': {
                    'slot_id': slot_id,
                    'notes': notes,
                    'user_id': request.user.id
                }
            })
            
            return JsonResponse({
                'order_id': order['id'],
                'amount': amount,
                'currency': 'INR',
                'key': settings.RAZORPAY_KEY_ID,
                'doctor_name': f'Dr. {doctor.name}',
                'user_name': request.user.get_full_name(),
                'user_email': request.user.email,
                'slot_id': slot_id,
                'notes': notes,
            })
        
        except Slot.DoesNotExist:
            return JsonResponse({'error': 'Slot not available!'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'error': 'POST only'})

# Verify payment and save appointment
@csrf_exempt
@login_required
def payment_success(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            payment_id = data.get('razorpay_payment_id')
            order_id = data.get('razorpay_order_id')
            signature = data.get('razorpay_signature')
            slot_id = data.get('slot_id')
            notes = data.get('notes', '')
            
            # Verify signature
            client = razorpay.Client(
                auth=(settings.RAZORPAY_KEY_ID,
                      settings.RAZORPAY_KEY_SECRET)
            )
            
            params = {
                'razorpay_order_id': order_id,
                'razorpay_payment_id': payment_id,
                'razorpay_signature': signature
            }
            
            client.utility.verify_payment_signature(params)
            
            # Payment verified! Save appointment
            slot = Slot.objects.get(id=slot_id, is_booked=False)
            patient, _ = Patient.objects.get_or_create(
                user=request.user,
                defaults={
                    'phone': '0000000000',
                    'age': 0,
                    'gender': 'Other'
                }
            )
            
            appointment = Appointment.objects.create(
                patient=patient,
                slot=slot,
                notes=notes,
                payment_id=payment_id,
                payment_status='Paid',
            )
            slot.is_booked = True
            slot.save()
            
            # Send confirmation email
            # 👇 ADD THIS LINE HERE
            print(f"📧 Sending email to: {request.user.email}")
            send_booking_email(request.user, appointment)
            
            return JsonResponse({
                'status': 'success',
                'message': 'Appointment booked successfully!'
            })
        
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            })
    
    return JsonResponse({'error': 'POST only'})

from django.core.mail import EmailMessage
from django.conf import settings as django_settings

def send_booking_email(user, appointment):
    try:
        subject = '✅ Appointment Confirmed — DocPro'
        
        body = f"""Dear {user.get_full_name()},

Your appointment has been confirmed! 🎉

━━━━━━━━━━━━━━━━━━━━━━━━
👨‍⚕️ Doctor     : Dr. {appointment.slot.doctor.name}
🏥 Specialist  : {appointment.slot.doctor.specialization.name}
📅 Date        : {appointment.slot.date.strftime('%A, %d %B %Y')}
🕐 Time        : {appointment.slot.time.strftime('%I:%M %p')}
💳 Payment ID  : {appointment.payment_id}
💰 Amount Paid : ₹{appointment.slot.doctor.fee}
━━━━━━━━━━━━━━━━━━━━━━━━

Please arrive 10 minutes before your appointment.

Stay healthy! 💙
DocPro Team
        """
        
        # Use EmailMessage instead of send_mail
        email = EmailMessage(
            subject=subject,
            body=body,
            from_email=django_settings.DEFAULT_FROM_EMAIL,
            to=[django_settings.EMAIL_HOST_USER],
        )
        email.send(fail_silently=False)
        print(f"✅ Email sent to {user.email}")
        
    except Exception as e:
        print(f"❌ Email error: {str(e)}")

def quiz_page(request):
    return render(request, 'quiz.html')

def get_quiz_question(request):
    if request.method == 'POST':
        import random
        topics = ['diet and nutrition', 'exercise and fitness', 'heart health', 
                  'general health', 'mental health', 'sleep hygiene', 'diabetes prevention']
        topic = random.choice(topics)
        
        client = Groq(api_key=settings.GROQ_API_KEY)
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{
                "role": "system",
                "content": "You are a health quiz generator. Always respond with ONLY valid JSON, no extra text."
            }, {
                "role": "user",
                "content": f"""Generate a health awareness quiz question about {topic}.
Return ONLY this JSON format:
{{
  "question": "question text here",
  "options": ["A) option1", "B) option2", "C) option3", "D) option4"],
  "correct": "A) option1",
  "explanation": "brief explanation why",
  "topic": "{topic}"
}}"""
            }],
            temperature=0.8,
            max_tokens=400
        )
        
        import re
        text = response.choices[0].message.content.strip()
        # Strip markdown code fences if present
        text = re.sub(r'^```json\s*|^```\s*|```$', '', text, flags=re.MULTILINE).strip()
        
        try:
            data = json.loads(text)
            return JsonResponse({'status': 'success', 'question': data})
        except:
            return JsonResponse({'status': 'error', 'message': 'Failed to parse question'})
    
    return JsonResponse({'error': 'POST only'})

# At top — add these imports
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
from .models import Patient, Doctor, Specialization, Slot, Appointment, UserProfile

# ── REGISTER (auto-detect doctor role from email pattern) ──────────────

# ── SLOT LOCK (called before payment) ─────────────────────────────────
@login_required
def lock_slot(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        slot_id = data.get('slot_id')
        try:
            with transaction.atomic():
                slot = Slot.objects.select_for_update().get(
                    id=slot_id, is_booked=False
                )
                # Check if locked by someone else
                if slot.is_locked() and slot.locked_by != request.user:
                    return JsonResponse({
                        'status': 'locked',
                        'message': 'This slot is being booked by someone else. Please choose another.'
                    })
                # Lock for 10 minutes for this user
                slot.locked_by = request.user
                slot.locked_until = timezone.now() + timedelta(minutes=10)
                slot.save()
                return JsonResponse({'status': 'locked_ok'})
        except Slot.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Slot not available'})
    return JsonResponse({'error': 'POST only'})


# ── DOCTOR DASHBOARD ───────────────────────────────────────────────────
@login_required
def doctor_dashboard(request):
    try:
        doctor = Doctor.objects.get(user=request.user)
    except Doctor.DoesNotExist:
        messages.error(request, 'Doctor profile not found.')
        return redirect('home')

    from datetime import date as dt
    today = dt.today()
    selected_date_str = request.GET.get('date', today.strftime('%Y-%m-%d'))

    try:
        from datetime import date
        selected_date = date.fromisoformat(selected_date_str)
    except ValueError:
        selected_date = today

    # Today's appointments
    todays_appointments = Appointment.objects.filter(
        slot__doctor=doctor,
        slot__date=selected_date,
    ).select_related('patient__user', 'slot').order_by('slot__time')

    # Stats
    total_today = todays_appointments.count()
    confirmed = todays_appointments.filter(status='Confirmed').count()
    completed = todays_appointments.filter(status='Completed').count()
    cancelled = todays_appointments.filter(status='Cancelled').count()

    # Upcoming slots for next 7 days
    from datetime import timedelta
    upcoming = Appointment.objects.filter(
        slot__doctor=doctor,
        slot__date__gt=selected_date,
        slot__date__lte=selected_date + timedelta(days=7),
        status='Confirmed'
    ).select_related('patient__user', 'slot').order_by('slot__date', 'slot__time')

    return render(request, 'doctor_dashboard.html', {
        'doctor': doctor,
        'appointments': todays_appointments,
        'selected_date': selected_date,
        'total_today': total_today,
        'confirmed': confirmed,
        'completed': completed,
        'cancelled': cancelled,
        'upcoming': upcoming,
        'all_slots': Slot.objects.filter(doctor=doctor, date__gte=today).order_by('date', 'time'),
        'today': today,
    })


# ── MARK APPOINTMENT COMPLETE (doctor action) ──────────────────────────
@login_required
def mark_complete(request, apt_id):
    try:
        doctor = Doctor.objects.get(user=request.user)
        apt = Appointment.objects.get(id=apt_id, slot__doctor=doctor)
        apt.status = 'Completed'
        apt.save()
        messages.success(request, 'Appointment marked as completed.')
    except Exception as e:
        messages.error(request, str(e))
    return redirect('doctor_dashboard')


# ── RESCHEDULE (patient action) ────────────────────────────────────────
@login_required
def reschedule_appointment(request, apt_id):
    if request.method == 'POST':
        new_slot_id = request.POST.get('new_slot_id')
        try:
            patient = Patient.objects.get(user=request.user)
            apt = Appointment.objects.get(id=apt_id, patient=patient, status='Confirmed')
            new_slot = Slot.objects.get(id=new_slot_id, is_booked=False)

            with transaction.atomic():
                # Free old slot
                old_slot = apt.slot
                old_slot.is_booked = False
                old_slot.locked_by = None
                old_slot.locked_until = None
                old_slot.save()

                # Book new slot
                new_slot.is_booked = True
                new_slot.locked_by = None
                new_slot.locked_until = None
                new_slot.save()

                apt.slot = new_slot
                apt.save()

            messages.success(request, f'Rescheduled to {new_slot.date} at {new_slot.time.strftime("%I:%M %p")}!')
        except Exception as e:
            messages.error(request, f'Reschedule failed: {str(e)}')
    return redirect('my_appointments')

# ── ADD SLOT (doctor action) ───────────────────────────────────────────
@login_required
def add_slot(request):
    if request.method == 'POST':
        try:
            doctor = Doctor.objects.get(user=request.user)
            slot_date = request.POST.get('date')
            slot_time = request.POST.get('time')

            from datetime import date as dt, datetime
            parsed_date = dt.fromisoformat(slot_date)
            parsed_time = datetime.strptime(slot_time, '%H:%M').time()

            # Prevent duplicate slots
            if Slot.objects.filter(doctor=doctor, date=parsed_date, time=parsed_time).exists():
                messages.error(request, 'This slot already exists!')
            else:
                Slot.objects.create(doctor=doctor, date=parsed_date, time=parsed_time)
                messages.success(request, f'Slot added: {parsed_date.strftime("%d %b %Y")} at {parsed_time.strftime("%I:%M %p")}')
        except Doctor.DoesNotExist:
            messages.error(request, 'Doctor profile not found.')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
    return redirect('doctor_dashboard')


# ── DELETE SLOT (doctor action) ────────────────────────────────────────
@login_required
def delete_slot(request, slot_id):
    # Allow GET — protected by @login_required + doctor ownership check below
    try:
        doctor = Doctor.objects.get(user=request.user)
        slot = Slot.objects.get(id=slot_id, doctor=doctor, is_booked=False)
        slot.delete()
        messages.success(request, 'Slot removed successfully.')
    except Slot.DoesNotExist:
        messages.error(request, 'Slot not found or already booked.')
    except Doctor.DoesNotExist:
        messages.error(request, 'Doctor profile not found.')
    except Exception as e:
        messages.error(request, f'Error: {str(e)}')
    return redirect('doctor_dashboard')