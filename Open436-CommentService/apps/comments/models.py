"""
Comment models
"""
from django.db import models
from django.utils import timezone


class Reply(models.Model):
    """
    回复模型
    注意：此表由 SQL 直接创建，Django 不管理迁移（managed=False）
    """

    id = models.AutoField(primary_key=True)

    post_id = models.IntegerField(
        db_index=True,
        help_text='帖子ID（关联M3 posts.id）'
    )

    author_id = models.IntegerField(
        db_index=True,
        help_text='作者ID（关联M1 users_auth.id）'
    )

    parent_id = models.IntegerField(
        blank=True,
        null=True,
        db_index=True,
        help_text='父回复ID（NULL表示顶级回复）'
    )

    content = models.TextField(
        help_text='回复内容（2-10000字符）'
    )

    floor_number = models.IntegerField(
        help_text='楼层号'
    )

    is_deleted = models.BooleanField(
        default=False,
        db_index=True,
        help_text='是否已删除'
    )

    edit_count = models.IntegerField(
        default=0,
        help_text='编辑次数'
    )

    last_edited_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text='最后编辑时间'
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text='创建时间'
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        help_text='更新时间'
    )

    class Meta:
        db_table = 'replies'
        managed = False
        ordering = ['post_id', 'floor_number']
        verbose_name = '回复'
        verbose_name_plural = '回复'

    def __str__(self):
        return f'Reply #{self.floor_number} on Post {self.post_id}'

    def soft_delete(self):
        """软删除"""
        self.is_deleted = True
        self.save(update_fields=['is_deleted', 'updated_at'])

    def can_edit(self, user_id, is_admin=False):
        """
        检查是否可以编辑
        5分钟内可以编辑，管理员无限制
        """
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
        """记录编辑"""
        self.edit_count += 1
        self.last_edited_at = timezone.now()
        self.save(update_fields=['edit_count', 'last_edited_at'])


class PostLike(models.Model):
    """
    帖子点赞模型
    注意：此表由 SQL 直接创建，Django 不管理迁移（managed=False）
    """

    id = models.AutoField(primary_key=True)

    post_id = models.IntegerField(
        db_index=True,
        help_text='帖子ID'
    )

    user_id = models.IntegerField(
        db_index=True,
        help_text='用户ID'
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text='点赞时间'
    )

    class Meta:
        db_table = 'post_likes'
        managed = False
        ordering = ['-created_at']
        verbose_name = '帖子点赞'
        verbose_name_plural = '帖子点赞'
        unique_together = [['post_id', 'user_id']]

    def __str__(self):
        return f'Like: User {self.user_id} -> Post {self.post_id}'


class PostFavorite(models.Model):
    """
    帖子收藏模型
    注意：此表由 SQL 直接创建，Django 不管理迁移（managed=False）
    """

    id = models.AutoField(primary_key=True)

    post_id = models.IntegerField(
        db_index=True,
        help_text='帖子ID'
    )

    user_id = models.IntegerField(
        db_index=True,
        help_text='用户ID'
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text='收藏时间'
    )

    class Meta:
        db_table = 'post_favorites'
        managed = False
        ordering = ['-created_at']
        verbose_name = '帖子收藏'
        verbose_name_plural = '帖子收藏'
        unique_together = [['post_id', 'user_id']]

    def __str__(self):
        return f'Favorite: User {self.user_id} -> Post {self.post_id}'


class ReplyLike(models.Model):
    """评论点赞模型"""

    id = models.AutoField(primary_key=True)
    reply_id = models.IntegerField(db_index=True, help_text='回复ID')
    user_id = models.IntegerField(db_index=True, help_text='用户ID')
    created_at = models.DateTimeField(auto_now_add=True, help_text='点赞时间')

    class Meta:
        db_table = 'reply_likes'
        managed = False
        ordering = ['-created_at']
        verbose_name = '评论点赞'
        verbose_name_plural = '评论点赞'
        unique_together = [['reply_id', 'user_id']]

    def __str__(self):
        return f'ReplyLike: User {self.user_id} -> Reply {self.reply_id}'


class ShareRecord(models.Model):
    """分享记录模型"""

    id = models.AutoField(primary_key=True)
    post_id = models.IntegerField(db_index=True, help_text='帖子ID')
    user_id = models.IntegerField(blank=True, null=True, db_index=True, help_text='用户ID')
    share_type = models.CharField(max_length=20, default='link', help_text='分享类型')
    created_at = models.DateTimeField(auto_now_add=True, help_text='分享时间')

    class Meta:
        db_table = 'share_records'
        managed = False
        ordering = ['-created_at']
        verbose_name = '分享记录'
        verbose_name_plural = '分享记录'

    def __str__(self):
        return f'Share: Post {self.post_id} via {self.share_type}'


class UserFollow(models.Model):
    """用户关注模型"""

    id = models.AutoField(primary_key=True)
    follower_id = models.IntegerField(db_index=True, help_text='关注者ID')
    following_id = models.IntegerField(db_index=True, help_text='被关注者ID')
    created_at = models.DateTimeField(auto_now_add=True, help_text='关注时间')

    class Meta:
        db_table = 'user_follows'
        managed = False
        ordering = ['-created_at']
        verbose_name = '用户关注'
        verbose_name_plural = '用户关注'
        unique_together = [['follower_id', 'following_id']]

    def __str__(self):
        return f'Follow: {self.follower_id} -> {self.following_id}'


class Topic(models.Model):
    """话题模型"""

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50, unique=True, help_text='话题名称')
    description = models.CharField(max_length=200, default='', blank=True, help_text='话题描述')
    posts_count = models.IntegerField(default=0, help_text='帖子数')
    followers_count = models.IntegerField(default=0, help_text='关注数')
    created_at = models.DateTimeField(auto_now_add=True, help_text='创建时间')

    class Meta:
        db_table = 'topics'
        managed = False
        ordering = ['-posts_count']
        verbose_name = '话题'
        verbose_name_plural = '话题'

    def __str__(self):
        return f'Topic: {self.name}'


class TopicFollow(models.Model):
    """话题关注模型"""

    id = models.AutoField(primary_key=True)
    user_id = models.IntegerField(db_index=True, help_text='用户ID')
    topic_id = models.IntegerField(db_index=True, help_text='话题ID')
    created_at = models.DateTimeField(auto_now_add=True, help_text='关注时间')

    class Meta:
        db_table = 'topic_follows'
        managed = False
        ordering = ['-created_at']
        verbose_name = '话题关注'
        verbose_name_plural = '话题关注'
        unique_together = [['user_id', 'topic_id']]

    def __str__(self):
        return f'TopicFollow: User {self.user_id} -> Topic {self.topic_id}'
