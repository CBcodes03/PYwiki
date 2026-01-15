from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.urls import reverse
import json, string, secrets, smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from django.db import connection

# --------------------------------------------
# 🔹 Helper: Get user role from DB
# --------------------------------------------
def get_user_role(user_id):
    with connection.cursor() as cursor:
        cursor.execute("SELECT role FROM auth_user WHERE id = %s", [user_id])
        row = cursor.fetchone()
    return row[0] if row else None

def get_user_role(user_id):
    with connection.cursor() as cursor:
        cursor.execute("SELECT role FROM auth_user WHERE id = %s", [user_id])
        row = cursor.fetchone()
    return row[0] if row else None


# --------------------------------------------
# 🔹 Generate Strong Random Password
# --------------------------------------------
def generate_strong_password(length=16):
    """
    Generate a strong random password with uppercase, lowercase, digits, and symbols.
    """
    if length < 8:
        length = 8  # enforce minimum secure length
    characters = string.ascii_letters + string.digits + string.punctuation
    return ''.join(secrets.choice(characters) for _ in range(length))


# --------------------------------------------
# 🔹 Send Invite Email
# --------------------------------------------
def invite(emailid, username, password, url):
    try:
        msg = MIMEMultipart()
        msg['From'] = "cbblogs58@gmail.com"
        msg['To'] = emailid
        msg['Subject'] = "Your PYWiki Account Credentials"

        body = f"""
        Hi {username},

        Your PYWiki account has been created successfully.
        You can log in using the credentials below:

        Username: {username}
        Password: {password}

        Login here: {url}

        Please change your password after logging in.
        """
        msg.attach(MIMEText(body, 'plain'))

        # SMTP setup (⚠️ use proper credentials in production)
        s = smtplib.SMTP('smtp.gmail.com', 587)
        s.starttls()
        s.login("cbblogs58@gmail.com", "orhn nagd xhpc swsq")  # Use app password, not normal Gmail password
        s.sendmail("cbblogs58@gmail.com", emailid, msg.as_string())
        s.quit()
        return True
    except Exception as e:
        print("Email Error:", e)
        return False


# --------------------------------------------
# 🔹 Login View
# --------------------------------------------
def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)
            messages.success(request, f"Welcome back, {username}!")
            return redirect("list_files_root")
        else:
            messages.error(request, "Invalid username or password!")
            return redirect("login")

    return render(request, "login.html")


# --------------------------------------------
# 🔹 Logout View
# --------------------------------------------
def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out successfully.")
    return redirect("login")


# --------------------------------------------
# 🔹 Get User List (JSON)
# --------------------------------------------
@login_required
def get_user_list(request):
    users = list(User.objects.values("id", "username"))
    return JsonResponse({"users": users})


# --------------------------------------------
# 🔹 Delete Users (with superuser protection)
# --------------------------------------------
@login_required
def delete_users(request):
    role = get_user_role(request.user.id)
    if role != 'admin':
        return JsonResponse({'error': "Permission denied — only admins can delete users."}, status=403)

    if request.method != "POST":
        return JsonResponse({'error': "Invalid request method."}, status=405)

    try:
        data = json.loads(request.body)
        ids = data.get('ids', [])
        if not ids:
            return JsonResponse({'info': "No users selected."})

        # Ensure all ids are integers
        ids = [int(i) for i in ids]

        # 🔹 Step 1: Get superuser IDs
        protected_ids = list(User.objects.filter(id__in=ids, is_superuser=True).values_list('id', flat=True))

        # 🔹 Step 2: Get users with role='admin' directly from DB (since it's not a Django field)
        with connection.cursor() as cursor:
            id_list = ",".join(map(str, ids))
            query = f"SELECT id FROM auth_user WHERE id IN ({id_list}) AND role='admin';"
            cursor.execute(query)
            admin_ids = [row[0] for row in cursor.fetchall()]
            protected_ids.extend(admin_ids)

        # 🔹 Step 3: Skip protected users
        protected_ids = list(set(protected_ids))  # remove duplicates
        ids_to_delete = [uid for uid in ids if uid not in protected_ids]

        warning_msg = None
        if protected_ids:
            warning_msg = f"Skipped {len(protected_ids)} admin/superuser account(s)."

        # 🔹 Step 4: Delete only allowed users
        deleted_count, _ = User.objects.filter(id__in=ids_to_delete).delete()

        response = {}
        if deleted_count:
            response['success'] = f"Deleted {deleted_count} user(s) successfully."
        else:
            response['info'] = "No users were deleted."

        if warning_msg:
            response['warning'] = warning_msg

        return JsonResponse(response)

    except Exception as e:
        return JsonResponse({'error': f"Error deleting users: {e}"}, status=500)



# --------------------------------------------
# 🔹 Create User View (with invite email)
# --------------------------------------------
@login_required
def create_user(request):
    role = get_user_role(request.user.id)
    if role != 'admin':
        return JsonResponse({"error": "Unauthorized — Only admins can create users."}, status=403)

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            username = data.get("username")
            email = data.get("email")
            role = data.get("role")

            if not username or not email:
                return JsonResponse({"error": "Username and email are required."}, status=400)

            if User.objects.filter(username=username).exists():
                return JsonResponse({"warning": f"User '{username}' already exists."}, status=200)

            password = generate_strong_password()
            user = User.objects.create_user(username=username, email=email, password=password)
            user.save()

            url = request.build_absolute_uri(reverse("login"))
            mail_sent = invite(email, username, password, url)

            if mail_sent:
                return JsonResponse({"success": f'User "{username}" created and email sent successfully!'})
            else:
                return JsonResponse({"warning": f'User "{username}" created, but email failed to send.'})

        except Exception as e:
            return JsonResponse({"error": f"Error creating user: {str(e)}"}, status=500)

    return JsonResponse({"error": "Invalid request method."}, status=405)


# --------------------------------------------
# 🔹 Admin Panel
# --------------------------------------------
@login_required
def admin_panel(request):
    return render(request, "admin.html")
