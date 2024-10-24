from django.shortcuts import render, redirect, get_object_or_404
from .models import *
from .forms import *
from django.contrib.auth import authenticate, logout, login
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator


# ---------------------------------- GENERAL -------------------------------------------

def home(request):
    all_posts = Post.objects.all().order_by('-time_created')
    text_posts = all_posts.filter(post_type=Post.TEXT)
    image_posts = all_posts.filter(post_type=Post.IMAGE)
    video_posts = all_posts.filter(post_type=Post.VIDEO)
    context = {
        'all_posts': all_posts,
        'text_posts': text_posts,
        'image_posts': image_posts,
        'video_posts': video_posts,
    }
    return render(request, 'main/home.html', context)



@login_required(login_url='login')
def inbox(request):
    incoming_messages = Message.objects.filter(receiver=request.user).order_by('-time_created')
    incoming_messages.filter(is_read=False).update(is_read=True)

    context = {
        'incoming_messages': incoming_messages
    }

    return render(request, 'main/profiles/inbox.html', context)


@login_required(login_url='login')
def delete_message(request, message_id):
    message = get_object_or_404(Message, id=message_id, receiver= request.user)
    message.delete()
    return redirect('inbox')


@login_required(login_url='login')
def search_posts(request):
    query = request.GET.get('q')
    print(query)
    search_results = []

    if query:
        search_results = Post.objects.filter(
            title__icontains=query
        ).order_by('-time_created')

    paginator = Paginator(search_results, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    print(search_results)

    context = {
        'query': query,
        'page_obj': page_obj,
    }
    return render(request, 'main/search_results.html', context)






# --------------------------- PROFILE -------------------------------------------

@login_required(login_url='login')
def profile(request, pk):
    viewed_user = get_object_or_404(User, pk=pk)
    viewed_profile = viewed_user.profile
    is_owner = request.user == viewed_user
    is_subscribed = request.user.profile.follows.filter(pk=viewed_profile.pk).exists() if request.user.is_authenticated else False

    user_posts = Post.objects.filter(user=viewed_user)
    user_posts_text = user_posts.filter(post_type=Post.TEXT)
    user_posts_image = user_posts.filter(post_type=Post.IMAGE)
    user_posts_video = user_posts.filter(post_type=Post.VIDEO)

    context = {
        'viewed_user': viewed_user,
        'viewed_profile': viewed_profile,
        'user_posts_text': user_posts_text,
        'user_posts_image': user_posts_image,
        'user_posts_video': user_posts_video,
        'is_owner': is_owner,
        'is_subscribed': is_subscribed,  # Pass subscription status to the template
    }

    return render(request, 'main/profiles/profile.html', context)



@login_required(login_url='login')
def chat(request, user_id):
    receiver = get_object_or_404(User, id=user_id)
    messages = Message.objects.filter(sender=request.user, receiver=receiver) | Message.objects.filter(sender=receiver, receiver=request.user)
    messages = messages.order_by('time_created')

    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.sender = request.user
            message.receiver = receiver
            message.save()
            return redirect('chat', user_id=user_id)
    else:
        form = MessageForm()
    context = {
        'receiver': receiver,
        'messages': messages,
        'form': form,
    }

    return render(request, 'main/profiles/chat.html', context)



@login_required(login_url='login')
def edit_profile(request, pk):
    user = get_object_or_404(User, pk=pk)
    profile = get_object_or_404(Profile, user=user)

    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=user)
        profile_form = ProfileUpdateForm(request.POST, request.FILES, instance=profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Your profile has been updated!')
            return redirect('profile', pk=user.pk)
    else:
        user_form = UserUpdateForm(instance=user)
        profile_form = ProfileUpdateForm(instance=profile)

    context = {
        'user_form': user_form,
        'profile_form': profile_form,
    }
    return render(request, 'main/profiles/edit_profile.html', context)


@login_required(login_url='login')
def subscribers_list_view(request, user_id):
    viewed_user = get_object_or_404(User, id=user_id)
    viewed_profile = get_object_or_404(Profile, user=viewed_user)

    # Get all subscribers
    subscribers = viewed_profile.followed_by.all()

    # Paginate subscribers
    paginator = Paginator(subscribers, 40)  # Show 10 subscribers per page
    page_number = request.GET.get('page')
    subscribers_page_obj = paginator.get_page(page_number)

    context = {
        'viewed_user': viewed_user,
        'viewed_profile': viewed_profile,
        'subscribers_page_obj': subscribers_page_obj,
    }
    return render(request, 'main/profiles/subscribers_list.html', context)


@login_required(login_url='login')
def subscriptions_list_view(request, user_id):
    viewed_user = get_object_or_404(User, id=user_id)
    viewed_profile = get_object_or_404(Profile, user=viewed_user)

    # Get all subscriptions
    subscriptions = viewed_profile.follows.all()

    # Paginate subscriptions
    paginator = Paginator(subscriptions, 40)  # Show 10 subscriptions per page
    page_number = request.GET.get('page')
    subscriptions_page_obj = paginator.get_page(page_number)

    context = {
        'viewed_user': viewed_user,
        'viewed_profile': viewed_profile,
        'subscriptions_page_obj': subscriptions_page_obj,
    }
    return render(request, 'main/profiles/subscriptions_list.html', context)



@login_required(login_url='login')
def edit_post(request, post_id):
    post = get_object_or_404(Post, id=post_id, user=request.user)

    if request.method == 'POST':
        form = EditPostForm(request.POST, request.FILES, instance=post)

        if form.is_valid():
            updated_post: Post = form.save(commit=False)

            if updated_post.post_type == Post.TEXT:
                updated_post.image = None
                updated_post.image = None
            elif updated_post.post_type == Post.IMAGE:
                updated_post.video = None
            elif updated_post.post_type == Post.VIDEO:
                updated_post.content = None
                updated_post.image = None

            updated_post.save()
            messages.success(request, "Post updated successfully!")
            return redirect('post_detail', post_id=post.id)
    else:
        form = EditPostForm(instance=post)

    return render(request, 'main/post/edit_post.html', {'form': form, 'post': post})



@login_required(login_url='login')
def delete_post(request, post_id):
    post = get_object_or_404(Post, id=post_id, user=request.user)
    if request.method == 'POST':
        post.delete()
        messages.success(request, "Post deleted successfully!")
        return redirect('home')
    return render(request, 'main/post/confirm_delete.html', {'post': post})



# --------------------------- MEDIA TOGGLES -> SUBSCRIBE & LIKE -------------------------------------------

@login_required(login_url='login')
def subscribe(request, pk):
    profile_to_subscribe = get_object_or_404(User, pk=pk)
    request.user.profile.follows.add(profile_to_subscribe.profile)
    return redirect(request.META.get('HTTP_REFERER', 'home'))



@login_required(login_url='login')
def unsubscribe(request, pk):
    profile_to_unsubscribe = get_object_or_404(User, pk=pk)
    request.user.profile.follows.remove(profile_to_unsubscribe.profile)
    return redirect(request.META.get('HTTP_REFERER', 'home'))



@login_required(login_url='login')
def toggle_like(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.user in post.likes.all():
        post.likes.remove(request.user)
        messages.success(request, f"You unliked \"{post.title}\".")
    else:
        post.likes.add(request.user)
        messages.success(request, f'You liked "{post.title}".')
    return redirect(request.META.get('HTTP_REFERER', 'home'))


# --------------------------- MEDIA -------------------------------------------

def media_text(request):
    ...


def media_image(request):
    ...


def media_video(request):
    ...


@login_required(login_url='login')
def add_post(request):
    if request.method == 'POST':
        post_type = request.POST.get('post_type')
        form = PostForm(request.POST, request.FILES, post_type=post_type)

        if form.is_valid():
            post = form.save(commit=False)
            post.user = request.user
            post.save()
            messages.success(request, "Successfully created a new post!")
            return redirect('home')
        else:
            messages.error(request, "Unsupported file extension.")
    else:
        form = PostForm(post_type=Post.TEXT)

    return render(request, 'main/media/add_post.html', {
        'text_form': PostForm(post_type=Post.TEXT),
        'image_form': PostForm(post_type=Post.IMAGE),
        'video_form': PostForm(post_type=Post.VIDEO),
    })




@login_required(login_url='login')
def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    comments = post.comments.all().order_by('-time_created')
    is_subscribed = post.user in request.user.profile.follows.all()

    if request.method == 'POST':
        if 'like' in request.POST:
            if request.user in post.likes.all():
                post.likes.remove(request.user)
                messages.success(request, f'You unliked "{post.title}"')
            else:
                post.likes.add(request.user)
                messages.success(request, f'You liked "{post.title}"')
        elif 'comment' in request.POST:
            comment_form = CommentForm(request.POST)
            if comment_form.is_valid():
                new_comment = comment_form.save(commit=False)
                new_comment.user = request.user
                new_comment.post = post
                new_comment.save()
                messages.success(request, 'Your comment has been posted.')
                return redirect('post_detail', post_id=post.id)

    comment_form = CommentForm()

    context = {
        'post': post,
        'is_subscribed': is_subscribed,
        'comments': comments,
        'comment_form': comment_form,
    }
    return render(request, 'main/media/post_detail.html', context)


# --------------------------- AUTH -------------------------------------------
def login_user(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, "You have been logged in!")
                return redirect('home')
            else:
                messages.error(request, "There was an error logging in! Please try again...")
                return redirect('login')
    else:
        form = LoginForm()
        return render(request, 'main/auth/login.html', {'form': form})


def signup_user(request):
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            login(request, user)
            messages.success(request, "You account has been created")
            return redirect('home')
        else:
            messages.error(request, "There was an error with your sign up. Please try again!")
            return redirect('signup')
    else:
        form = SignUpForm()
        return render(request, 'main/auth/signup.html', {'form': form})


@login_required(login_url='login')
def logout_user(request):
    logout(request)
    return redirect('login')

