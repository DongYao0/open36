"""
Post models
"""
from django.db import models
from django.utils import timezone


class Post(models.Model):
    """
    帖子模型
    注意：此表由 SQL 直接创建，Django 不管理迁移（managed=False）
    """

    STATUS_PUBLISHED = 'published'
    STATUS_DELETED = 'deleted'
    STATUS_CHOICES = [
        (STATUS_PUBLISHED, '已发布'),
        (STATUS_DELETED, '已删除'),
    ]

    PIN_NONE = 'none'
    PIN_GLOBAL = 'global'
    PIN_SECTION = 'section'
    PIN_CHOICES = [
        (PIN_NONE, '未置顶'),
        (PIN_GLOBAL, '全局置顶'),
        (PIN_SECTION, '板块置顶'),
    ]

    id = models.AutoField(primary_key=True)

    title = models.CharField(
        max_length=100,
        help_text='帖子标题（5-100字符）'
    )

    content = models.TextField(
        help_text='帖子内容（支持富文本）'
    )

    author_id = models.IntegerField(
        help_text='作者ID（关联M1 users_auth.id）'
    )

    section_id = models.IntegerField(
        help_text='板块ID（关联M5 sections.id）'
    )

    is_pinned = models.BooleanField(
        default=False,
        db_index=True,
        help_text='是否置顶'
    )

    pin_type = models.CharField(
        max_length=20,
        choices=PIN_CHOICES,
        default=PIN_NONE,
        db_index=True,
        help_text='置顶类型'
    )

    views_count = models.IntegerField(
        default=0,
        help_text='浏览量'
    )

    replies_count = models.IntegerField(
        default=0,
        help_text='回复数（由M4评论服务同步更新）'
    )

    likes_count = models.IntegerField(
        default=0,
        help_text='点赞数（由M4评论服务同步更新）'
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PUBLISHED,
        db_index=True,
        help_text='帖子状态'
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

    last_edited_by = models.IntegerField(
        blank=True,
        null=True,
        help_text='最后编辑者ID'
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
        db_table = 'posts'
        managed = False
        ordering = ['-is_pinned', '-created_at']
        verbose_name = '帖子'
        verbose_name_plural = '帖子'

    def __str__(self):
        return f'{self.title[:30]} (ID: {self.id})'

    def __repr__(self):
        return f'<Post: {self.id}>'

    def soft_delete(self):
        """软删除"""
        self.status = self.STATUS_DELETED
        self.save(update_fields=['status', 'updated_at'])

    def restore(self):
        """恢复帖子"""
        self.status = self.STATUS_PUBLISHED
        self.save(update_fields=['status', 'updated_at'])

    def pin(self, pin_type):
        """置顶"""
        self.is_pinned = True
        self.pin_type = pin_type
        self.save(update_fields=['is_pinned', 'pin_type', 'updated_at'])

    def unpin(self):
        """取消置顶"""
        self.is_pinned = False
        self.pin_type = self.PIN_NONE
        self.save(update_fields=['is_pinned', 'pin_type', 'updated_at'])

    def increment_views(self):
        """原子性增加浏览量"""
        from django.db.models import F
        Post.objects.filter(id=self.id).update(views_count=F('views_count') + 1)
        self.refresh_from_db()

    def can_edit(self, user_id, is_admin=False):
        """
        检查用户是否可以编辑帖子
        24小时内无限制，之后最多5次（管理员除外）
        """
        if is_admin:
            return True
        if self.author_id != user_id:
            return False
        created_at = self.created_at
        if timezone.is_naive(created_at):
            created_at = timezone.make_aware(created_at)
        hours_since_created = (timezone.now() - created_at).total_seconds() / 3600
        if hours_since_created <= 24:
            return True
        return self.edit_count < 5

    def record_edit(self, editor_id):
        """记录编辑"""
        self.edit_count += 1
        self.last_edited_at = timezone.now()
        self.last_edited_by = editor_id
        self.save(update_fields=['edit_count', 'last_edited_at', 'last_edited_by'])


class PostEditHistory(models.Model):
    """
    帖子编辑历史
    注意：此表由 SQL 直接创建，Django 不管理迁移（managed=False）
    """

    id = models.AutoField(primary_key=True)

    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        db_column='post_id',
        related_name='edit_history',
        help_text='关联帖子'
    )

    title = models.CharField(
        max_length=100,
        help_text='当时的标题'
    )

    content = models.TextField(
        help_text='当时的内容'
    )

    section_id = models.IntegerField(
        help_text='当时的板块ID'
    )

    edited_by = models.IntegerField(
        help_text='编辑者ID'
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text='编辑时间'
    )

    class Meta:
        db_table = 'post_edit_history'
        managed = False
        ordering = ['-created_at']
        verbose_name = '编辑历史'
        verbose_name_plural = '编辑历史'

    def __str__(self):
        return f'History #{self.id} for Post {self.post_id}'
