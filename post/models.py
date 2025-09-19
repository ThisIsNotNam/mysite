from django.db import models
from django.contrib.auth.models import User

class Post(models.Model):
    title = models.CharField(max_length=255)
    body = models.TextField()
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)

    def get_upvotes(self):
        return self.votes.filter(voteType='up').count()

    def get_downvotes(self):
        return self.votes.filter(voteType='down').count()

    def get_user_vote(self, user):
        vote = self.votes.filter(user=user).first()
        return vote.voteType if vote else None
    
    def get_bookmarks_count(self):
        return self.bookmarks.count()

    def is_bookmarked_by(self, user):
        return self.bookmarks.filter(user=user).exists()


class Vote(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, related_name='votes', on_delete=models.CASCADE)
    voteType = models.CharField(max_length=10, choices=[('up', 'Upvote'), ('down', 'Downvote')])

    class Meta:
        unique_together = ('user', 'post')

class Bookmark(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey("Post", related_name="bookmarks", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "post")

    def __str__(self):
        return f"{self.user.username} bookmarked {self.post.title}"