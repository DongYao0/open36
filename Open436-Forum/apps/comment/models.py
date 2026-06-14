"""
Comment models
"""
from django.db import models
from django.utils import timezone


class Reply(models.Model):
    """回复模型"""
    id = models.AutoField(primary_key=True)
    post_id = models.IntegerField(db_index=True, help_text='帖子ID（关联 posts.id）')
    author_id = models.IntegerField(db_index=True, help_text='作者ID（关联 users_auth.id）')
    parent_id = models.IntegerField(blank=True, null=True, db_index=True, help_text='父回复ID')
    content = models.TextField(help_text='回复内容（2-10000字符）')
    floor_number = models.IntegerField(help_text='楼层号')
    is_deleted = models.BooleanField(default=False, db_index=True, help_text='是否已删除')
    edit_count = models.IntegerField(default=0, help_text='编辑次数')
    last_edited_at = models.DateTimeField(blank=True, null=True, help_text='最后编辑时间')
    created_at = models.DateTimeField(auto_now_add=True, help_text='创建时间')
    updated_at = models.DateTimeField(auto_now=True, help_text='更新时间')

    class Meta:
        db_table = 'replies'
        managed = False
        ordering = ['post_id', 'floor_number']
        verbose_name = '回复'
        verbose_name_plural = '回复'

    def __str__(self):
        return f'Reply #{self.floor_number} on Post {self.post_id}'

    def soft_delete(self):
        self.is_deleted = True
        self.save(update_fields=['is_deleted', 'updated_at'])

    def can_edit(self, user_id, is_admin=False):
        if is_admin:
            return True
        if self.author_id != user_id:
            return False
        created = self.created_at
        if timezone.is_naive(created):
            created = timezone.make_aware(created)
        minutes_since = (timezone.now() - created).total_seconds() / 60
        return minutes_since <= 5

    def record_edit(self):
        self.edit_count += 1
        self.last_edited_at = timezone.now()
        self.save(update_fields=['edit_count', 'last_edited_at'])


class PostLike(models.Model):
    """帖子点赞模型"""
    id = models.AutoField(primary_key=True)
    post_id = models.IntegerField(db_index=True)
    user_id = models.IntegerField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'post_likes'
        managed = False
        ordering = ['-created_at']
        unique_together = [['post_id', 'user_id']]


class PostFavorite(models.Model):
    """帖子收藏模型"""
    id = models.AutoField(primary_key=True)
    post_id = models.IntegerField(db_index=True)
    user_id = models.IntegerField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'post_favorites'
        managed = False
        ordering = ['-created_at']
        unique_together = [['post_id', 'user_id']]


class ReplyLike(models.Model):
    """评论点赞模型"""
    id = models.AutoField(primary_key=True)
    reply_id = models.IntegerField(db_index=True)
    user_id = models.IntegerField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'reply_likes'
        managed = False
        ordering = ['-created_at']
        unique_together = [['reply_id', 'user_id']]


class ShareRecord(models.Model):
    """分享记录模型"""
    id = models.AutoField(primary_key=True)
    post_id = models.IntegerField(db_index=True)
    user_id = models.IntegerField(blank=True, null=True, db_index=True)
    share_type = models.CharField(max_length=20, default='link')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'share_records'
        managed = False
        ordering = ['-created_at']


class UserFollow(models.Model):
    """用户关注模型"""
    id = models.AutoField(primary_key=True)
    follower_id = models.IntegerField(db_index=True)
    following_id = models.IntegerField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'user_follows'
        managed = False
        ordering = ['-created_at']
        unique_together = [['follower_id', 'following_id']]


class Topic(models.Model):
    """话题模型"""
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50, unique=True)
    description = models.CharField(max_length=200, default='', blank=True)
    posts_count = models.IntegerField(default=0)
    followers_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'topics'
        managed = False
        ordering = ['-posts_count']


class TopicFollow(models.Model):
    """话题关注模型"""
    id = models.AutoField(primary_key=True)
    user_id = models.IntegerField(db_index=True)
    topic_id = models.IntegerField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'topic_follows'
        managed = False
        ordering = ['-created_at']
        unique_together = [['user_id', 'topic_id']]
