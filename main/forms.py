from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .models import *
import os
from django.utils.deconstruct import deconstructible


@deconstructible
class FileValidator:
    error_message = {
        'max_size': "Ensure this file size is not greater than %(max_size)s. You file size is %(size)s.",
        'content_type': "Files of type %(content_type)s are not supported."
    }

    def __init__(self, max_size=None, content_types=None):
        self.max_size = max_size
        self.content_types = content_types

    def __call__(self, value):
        if self.max_size and value.size > self.max_size:
            raise ValidationError(
                self.error_message['max_size'],
                code='max_size',
                params={'max_size': self.max_size, 'size': value.size}
            )

        if self.content_types and value.content_type not in self.content_types:
            raise ValidationError(
                self.error_message['content_type'],
                code='content_type',
                params={'content_type': value.content_type},
            )


# ------------------------------ Media --------------------------------

class PostForm(forms.ModelForm):
    post_type = forms.ChoiceField(choices=Post.POST_TYPES, widget=forms.HiddenInput())

    class Meta:
        model = Post
        fields = ['title', 'content', 'image', 'video', 'post_type']

    def __init__(self, *args, **kwargs):
        post_type = kwargs.pop('post_type', None)
        super().__init__(*args, **kwargs)
        print(f"Form init with {post_type}")
        if post_type:
            self.fields['post_type'].initial = post_type
            if post_type == Post.TEXT:
                self.fields['image'].widget = forms.HiddenInput()
                self.fields['video'].widget = forms.HiddenInput()
            elif post_type == Post.IMAGE:
                self.fields['video'].widget = forms.HiddenInput()
            elif post_type == Post.VIDEO:
                self.fields['content'].widget = forms.HiddenInput()
                self.fields['image'].widget = forms.HiddenInput()

                self.fields['video'].validators = [
                    FileValidator(
                        max_size=10*1024*1024,
                        content_types=[
                            'video/mp4',
                            'video/avi',
                            'video/mpeg',
                            'video/quicktime',
                        ]
                    )
                ]

    def clean_video(self):
        video = self.cleaned_data.get('video', None)

        if video:
            content_type = video.content_type.split('/')[0]
            if content_type != 'video':
                raise ValidationError('Uploaded file is not a video')

            valid_extensions = ['.mp4', '.avi', '.mpeg', '.mov', '.wmv']
            ext = os.path.splitext(video.name)[1].lower()
            if ext not in valid_extensions:
                raise ValidationError(f"Unsupported file extension. Supported extensions are: {valid_extensions}")
            return video



class CommentForm(forms.ModelForm):
    content = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Write your comment...',
            'rows': 3,
        }),
        max_length=2000,
    )

    class Meta:
        model = Comment
        fields = ['content']




class EditPostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'post_type', 'content', 'image', 'video']

    def clean(self):
        cleaned_data = super().clean()
        post_type = cleaned_data.get('post_type')

        if post_type == Post.TEXT and not cleaned_data.get('content'):
            self.add_error('content', "Content is required for text posts.")
        elif post_type == Post.IMAGE and not cleaned_data.get('image'):
            self.add_error('image', "An image is required for image posts.")
        elif post_type == Post.VIDEO:
            video = cleaned_data.get('video')
            if not video:
                self.add_error('video', "A video is required for video posts.")
            elif video.size > Post.video_size_limit:
                self.add_error('video',
                               f"Video file size exceeds the limit of {Post.video_size_limit / (1024 * 1024)} MB.")

        return cleaned_data






class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'placeholder': "Message..."}),
        }







# ------------------------------ Authentication --------------------------------

class LoginForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'})
    )


class SignUpForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'})
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm Password'})
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}),
            'email': forms.TextInput(attrs={'class': 'form-control', 'placeholder': "Email"}),
        }
        error_messages = {
            'username': {
                'required': "Username is required",
            },
            'email': {
                'required': "Email is required",
                'invalid': "Enter a valid email address",
            },
            'password': {
                'required': "Password is required",
            }
        }


    def clean_confirm_password(self):
        password = self.cleaned_data.get('password')
        confirm_password = self.cleaned_data.get('confirm_password')

        if password != confirm_password:
            raise ValidationError('Passwords do not match!')
        return confirm_password

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("Email already exists!")
        return email


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username']


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['profile_image', 'country', 'bio']
