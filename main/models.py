from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone



class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    content = models.TextField()
    time_created = models.DateTimeField(default=timezone.now)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"Message from {self.sender.username} to {self.receiver.username}"

    def delete_message(self):
        self.delete()

    def mark_as_read(self):
        self.is_read = True
        self.save()



class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    follows = models.ManyToManyField("self",
                                     related_name='followed_by',
                                     symmetrical=False,
                                     blank=True)
    last_entered = models.DateTimeField(auto_now=True)
    profile_image = models.ImageField(upload_to='profile_images/%Y/%m/%d', default='profile_images/default.png', verbose_name='Profile Image')
    bio = models.CharField(max_length=500)
    country = models.CharField(max_length=100)

    def __str__(self):
        return self.user.username



class Post(models.Model):
    TEXT = 'text'
    IMAGE = 'image'
    VIDEO = 'video'

    POST_TYPES = [
        (TEXT, 'Text'),
        (IMAGE, 'Image'),
        (VIDEO, 'Video'),
    ]

    title = models.CharField(max_length=255)
    post_type = models.CharField(max_length=10, choices=POST_TYPES, default=TEXT)
    content = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='post_images/%Y/%m/%d', blank=True, null=True)
    video = models.FileField(upload_to='post_videos/%Y/%m/%d', blank=True, null=True)
    video_size_limit = models.PositiveIntegerField(default=10485760)  # 10 MB in bytes
    time_created = models.DateTimeField(auto_now_add=True)

    user = models.ForeignKey(User, on_delete=models.DO_NOTHING, related_name='posts')
    likes = models.ManyToManyField(User, related_name='liked_posts', blank=True)

    def clean(self):
        if self.post_type == self.TEXT and not self.content:
            raise ValidationError("Content is required for text posts.")
        elif self.post_type == self.IMAGE and not self.image:
            raise ValidationError("An image is required for image posts.")
        elif self.post_type == self.VIDEO and not self.video:
            raise ValidationError("A video is required for video posts.")
        if self.video and self.video.size > self.video_size_limit:
            raise ValidationError(f"Video file size exceeds the limit of {self.video_size_limit / (1024 * 1024)} MB.")

    def save(self, *args, **kwargs):
        if self.post_type == self.TEXT:
            self.image = None
            self.video = None
        elif self.post_type == self.IMAGE:
            self.video = None
        elif self.post_type == self.VIDEO:
            self.content = None
            self.image = None
            if self.video and self.video.size > self.video_size_limit:
                raise ValueError("Video file size exceeds the limit of 10 MB")

        super(Post, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} ({self.get_post_type_display()}) by {self.user.username}"

    def total_likes(self):
        return self.likes.count()


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField()
    time_created = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Comment by {self.user.username} on {self.post.title}"
