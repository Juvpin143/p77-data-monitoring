from email.mime.image import MIMEImage
from urllib import request
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib import messages
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.utils.encoding import force_bytes
from .forms import RegisterForm
from django.contrib.auth import logout
from django.contrib.messages import get_messages
from django.contrib.auth.views import LoginView
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMultiAlternatives
from django.utils.html import strip_tags
from django.conf import settings
from datetime import timedelta
from django.utils.timezone import now
from django.urls import reverse
import os

User = get_user_model()

def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)

        if form.is_valid():
            username = form.cleaned_data.get('username')
            email = form.cleaned_data.get('email')

            # 🔥 Delete expired unactivated accounts with same username or email
            User.objects.filter(
                username=username,
                is_active=False,
                is_activated=False
            ).delete()
            User.objects.filter(
                email=email,
                is_active=False,
                is_activated=False
            ).delete()

            user = form.save(commit=False)
            user.role = "staff"
            user.is_active = False
            user.is_activated = False
            user.activation_sent_at = now()
            user.save()

            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            domain = request.get_host()

            try:
                send_activation_email(user, domain, uid, token)
            except Exception:
                pass

            messages.success(request, "Account created successfully, please check your email to activate your account.")
            return redirect('account:login')

        # ✅ Show specific error if username/email already EXISTS and ACTIVATED
        else:
            username = request.POST.get('username')
            email = request.POST.get('email')
            if User.objects.filter(username=username, is_activated=True).exists():
                messages.error(request, "Username already taken.")
            elif User.objects.filter(email=email, is_activated=True).exists():
                messages.error(request, "Email already registered.")

    else:
        form = RegisterForm()

    return render(request, 'account/register.html', {'form': form})

def activate(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        if user.activation_sent_at:
            if now() > user.activation_sent_at + timedelta(minutes=3):
                messages.error(request, "Activation link expired (3 minutes).")
                return redirect(reverse('account:login'))

        if not user.is_active:
            user.is_active = True
            user.is_activated = True
            user.save()
            messages.success(request, 'Account has been activated')
        else:
            messages.error(request, 'Your account is already active. Please login again!')
    else:
        messages.error(request, 'Activation link is invalid. Please check your email and try again.')
    return redirect(reverse('account:login'))

def send_activation_email(user, domain, uid, token):
    subject = 'Activate your P77-Data-Monitoring Account'
    from_email = settings.DEFAULT_FROM_EMAIL
    to = [user.email]

    html_content = render_to_string('account/activate_account.html', {
        'user': user,
        'domain': domain,
        'uid': uid,
        'token': token,
    })

    text_content = strip_tags(html_content)

    email = EmailMultiAlternatives(subject, text_content, from_email, to)
    email.attach_alternative(html_content, 'text/html')

    logo_path = os.path.join(settings.MEDIA_ROOT, 'img', 'p77_logo.png')

    if os.path.exists(logo_path):
        with open(logo_path, 'rb') as f:
            logo = MIMEImage(f.read())
            logo.add_header('Content-ID', '<p77_logo>')
            logo.add_header('Content-Disposition', 'attachment', filename='p77_logo.png')
            email.attach(logo)

    email.send()

def forgot_password(request):
    if request.method == 'POST':
        email = request.POST.get('email')

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            messages.success(request, "Check your email and reset your password")
            return redirect(reverse('account:forgot_password'))

        domain = request.get_host()
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)

        send_pass_reset_email(user, domain, uid, token)

        messages.success(request, "Password reset email has been sent successfully!")
        return redirect(reverse('account:login'))

    return render(request, 'account/forgot_password.html')

def send_pass_reset_email(user, domain, uid, token):
    subject = "Reset your P77 Password"
    from_email = settings.DEFAULT_FROM_EMAIL

    html_content = render_to_string('account/reset_password_email.html', {
        'user': user,
        'domain': domain,
        'uid': uid,
        'token': token,
    })

    text_content = strip_tags(html_content)

    email = EmailMultiAlternatives(subject, text_content, from_email, [user.email])
    email.attach_alternative(html_content, 'text/html')

    logo_path = os.path.join(settings.MEDIA_ROOT, 'img', 'p77_logo.png')

    if os.path.exists(logo_path):
        with open(logo_path, 'rb') as f:
            logo = MIMEImage(f.read())
            logo.add_header('Content-ID', '<p77_logo>')
            email.attach(logo)

    email.send()

def password_reset(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except:
        user = None

    if user is not None and default_token_generator.check_token(user, token):

        if request.method == 'POST':
            password = request.POST.get("password")
            confirm_password = request.POST.get("confirm_password")

            if password == confirm_password:
                user.set_password(password)
                user.save()
                messages.success(request, "Password has been reset successfully!")
                return redirect(reverse('account:login'))
            else:
                messages.error(request, 'Passwords do not match.')

        return render(request, 'account/password_reset.html')

    else:
        messages.error(request, 'Invalid or expired link.')
        return redirect(reverse('account:login'))

class CustomLoginView(LoginView):
    template_name = 'account/login.html'

    def get_success_url(self):
        user = self.request.user
        if user.is_superuser or user.role in ['admin', 'viewer']:
            messages.success(self.request, f"Welcome back {user.username}")
            return reverse_lazy('adminpanel:admin_dashboard')
        else:
            messages.success(self.request, f"Welcome back {user.username}")
            return reverse_lazy('staff_dashboard')

def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out")
    return redirect(reverse('account:login'))

