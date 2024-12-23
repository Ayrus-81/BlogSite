from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, update_session_auth_hash
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from .models import UserProfile, BlogPost
from .forms import BlogPostForm, CommentForm


# General Views
def index_view(request):
    return render(request, 'index.html')


def home_view(request):
    return render(request, 'home.html')


def register_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        first_name = request.POST.get('firstname')
        last_name = request.POST.get('lastname')
        email = request.POST.get('email')
        contact = request.POST.get('contact')
        password = request.POST.get('password')
        password1 = request.POST.get('password1')
        profile_pic = request.FILES.get('profilepic')

        if password == password1:
            if User.objects.filter(username=username).exists():
                messages.error(request, "Username already taken.")
                return redirect('register')
            if User.objects.filter(email=email).exists():
                messages.error(request, "Email already registered.")
                return redirect('register')

            user = User.objects.create_user(
                username=username,
                first_name=first_name,
                last_name=last_name,
                email=email,
                password=password
            )

            UserProfile.objects.create(user=user, contact_number=contact, profile_pic=profile_pic)

            messages.success(request, "Registration successful. You can now log in.")
            return redirect('login')
    return render(request, 'user/register.html')


@user_passes_test(lambda u: True, login_url='/login/')
def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)
        if user:
            if user.is_staff:
                login(request, user)
                messages.success(request, "Admin login successful!")
                return redirect('admin_dashboard')
            else:
                login(request, user)
                messages.success(request, "Login successful!")
                return redirect('blog_post_list')
        else:
            messages.error(request, "Invalid username or password.")

    return render(request, 'admin/admin_login.html' if request.GET.get('admin') else 'user/login.html')


@login_required
def profile_view(request):
    user_profile, _ = UserProfile.objects.get_or_create(user=request.user)
    return render(request, 'user/profile.html', {'user': request.user, 'profile': user_profile})


@login_required
def profile_update(request):
    user = request.user
    user_profile = user.userprofile

    if request.method == 'POST':
        user.username = request.POST.get('username')
        user.first_name = request.POST.get('firstname')
        user.last_name = request.POST.get('lastname')
        user.email = request.POST.get('email')
        user.save()

        user_profile.contact_number = request.POST.get('contact', user_profile.contact_number)
        profile_pic = request.FILES.get('profilepic')
        if profile_pic:
            user_profile.profile_pic = profile_pic
        user_profile.save()

        messages.success(request, "Your profile has been updated successfully.")
        return redirect('profile')

    return render(request, 'user/update_profile.html', {'user': user, 'profile': user_profile})


def forgot_password(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        username = request.POST.get('username')
        user = User.objects.filter(email=email, username=username).first()

        if user:
            uid = urlsafe_base64_encode(str(user.pk).encode())
            token = default_token_generator.make_token(user)
            reset_link = request.build_absolute_uri(
                reverse('password_reset', kwargs={'uidb64': uid, 'token': token})
            )

            send_mail(
                "Password Reset",
                f"Click the link to reset your password: {reset_link}",
                settings.EMAIL_HOST_USER,
                [email],
            )

            messages.success(request, "A password reset link has been sent to your email.")
        else:
            messages.error(request, "No user found with that email and username combination.")

        return redirect('password_reset_done')
    return render(request, 'user/forgot_password.html')


def reset_password(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user and default_token_generator.check_token(user, token):
        if request.method == 'POST':
            new_password = request.POST.get('password')
            confirm_password = request.POST.get('confirm_password')

            if new_password == confirm_password:
                user.set_password(new_password)
                user.save()
                update_session_auth_hash(request, user)
                messages.success(request, "Your password has been reset successfully!")
                return redirect('password_reset_complete')
            else:
                messages.error(request, "Passwords do not match. Please try again.")
        return render(request, 'user/reset_password.html')
    else:
        messages.error(request, "The password reset link is invalid or has expired.")
        return redirect('password_reset_invalid')


# Blog Views

@login_required
def create_blog_post(request):
    if request.method == "POST":
        form = BlogPostForm(request.POST, request.FILES)
        if form.is_valid():
            blog_post = form.save(commit=False)
            blog_post.author = request.user
            blog_post.save()
            messages.success(request, "Blog post created successfully!")
            return redirect('my_blog_post_list')
    else:
        form = BlogPostForm()
    return render(request, 'user/create_blog_post.html', {'form': form})


@login_required
def edit_blog_post(request, id):
    blog_post = get_object_or_404(BlogPost, id=id)

    if request.method == 'POST':
        form = BlogPostForm(request.POST, request.FILES, instance=blog_post)
        if form.is_valid():
            form.save()
            return redirect('my_blog_post_list')
    else:
        form = BlogPostForm(instance=blog_post)

    return render(request, 'user/edit_blog_post.html', {'form': form, 'blog_post': blog_post})


@login_required
def delete_blog_post(request, id):

    blog_post = get_object_or_404(BlogPost, id=id)

    if blog_post.author != request.user:

        return redirect('my_blog_post_list')

    if request.method == 'POST':

        blog_post.delete()

        return redirect('my_blog_post_list')

    return redirect('my_blog_post_list')


def blog_post_list(request):
    blog_posts = BlogPost.objects.filter(is_published=True).order_by('-created_at')
    paginator = Paginator(blog_posts, 10)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'user/blog_post_list.html', {'page_obj': page_obj})


@login_required
def add_comment(request, post_id):

    blog_post = get_object_or_404(BlogPost, id=post_id, is_published=True)

    if request.method == "POST":
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.blog_post = blog_post
            comment.user = request.user
            comment.save()

            if blog_post.author != request.user:
                send_mail(
                    subject=f"New Comment on Your Blog Post: {blog_post.title}",
                    message=f"{request.user.username} commented on your post:\n\n{comment.content}",
                    from_email="noreply@example.com",
                    recipient_list=[blog_post.author.email],
                )

            messages.success(request, "Comment added successfully!")
            return redirect('blog_post_detail', post_id=blog_post.id)
    else:
        form = CommentForm()

    return render(request, 'user/add_comment.html', {'form': form, 'blog_post': blog_post})


def blog_post_detail(request, post_id):
    blog_post = get_object_or_404(BlogPost, id=post_id)
    comments = blog_post.comments.all()
    return render(request, 'user/blog_post_details.html', {'blog_post': blog_post, 'comments': comments})


@login_required
def my_blog_post_list(request):
    blog_posts = BlogPost.objects.filter(author=request.user, is_deleted=False).order_by('-created_at')
    paginator = Paginator(blog_posts, 10)
    page_obj = paginator.get_page(request.GET.get('page'))

    if not blog_posts.exists():
        messages.info(request, "You haven't created any blog posts yet.")

    return render(request, 'user/my_blog_post_list.html', {'page_obj': page_obj})

# Check if the user is an admin
def is_admin(user):
    return user.is_staff


@user_passes_test(is_admin, login_url='/login/')  # Redirect to default login if not admin
def admin_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)

        if user is not None and user.is_staff:
            login(request, user)
            return redirect('admin_dashboard')  # Redirect to admin dashboard
        else:
            messages.error(request, 'Invalid login credentials or not an admin user.')
            return redirect('admin_login')  # Stay on the login page if failed

    return render(request, 'admin/admin_login.html')


@user_passes_test(is_admin, login_url='/login/')
def admin_dashboard(request):
    return render(request, 'admin/admin_dashboard.html')


@user_passes_test(is_admin, login_url='/login/')
def user_list(request):
    # Get all users excluding admin users (staff or superuser)
    users = User.objects.exclude(is_staff=True, is_superuser=True)  # Exclude admin users
    return render(request, 'admin/user_list.html', {'users': users})


@user_passes_test(is_admin, login_url='/login/')
def block_user(request, user_id):
    user = get_object_or_404(User, id=user_id)

    # If the user is active, block them; otherwise, unblock them
    if user.is_active:
        user.is_active = False  # Block the user
        action = "blocked"
    else:
        user.is_active = True  # Unblock the user
        action = "unblocked"

    user.save()

    # Redirect with a message about the action taken
    return redirect('user_list')


@user_passes_test(is_admin, login_url='/login/')
def delete_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    user.is_active = False  # Disable the user account
    user.save()
    return redirect('user_list')


@user_passes_test(is_admin, login_url='/login/')
def post_list(request):
    posts = BlogPost.objects.all()
    return render(request, 'admin/post_list.html', {'posts': posts})


@user_passes_test(is_admin, login_url='/login/')
def delete_post(request, post_id):
    # Get the post or return a 404 error if not found
    post = get_object_or_404(BlogPost, id=post_id)

    # Handle the deletion for POST requests
    if request.method == "POST":
        post.delete()  # Delete the post
        return redirect('post_list')  # Redirect back to the post list after deletion

    # If method is not POST, redirect to the post list (you could show an error message here too)
    return redirect('post_list')

# Toggle publish status of a post
@user_passes_test(is_admin, login_url='/login/')
def toggle_publish_post(request, post_id):
    post = get_object_or_404(BlogPost, id=post_id)
    post.is_published = not post.is_published  # Toggle the published status
    post.save()
    return redirect('post_list')
