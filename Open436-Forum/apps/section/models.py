"""
Section models
"""
from django.db import models
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator


class Section(models.Model):
    """板块模型"""
    id = models.AutoField(primary_key=True)
    slug = models.SlugField(max_length=20, unique=True, db_index=True,
        validators=[RegexValidator(regex=r'^[a-z0-9_]+$', message='板块标识只能包含小写字母、数字和下划线')],
        help_text='板块标识，用于 URL（3-20个字符）')
    name = models.CharField(max_length=50, unique=True, help_text='板块名称（2-50个字符）')
    description = models.TextField(blank=True, null=True, help_text='板块描述')
    icon_file_id = models.UUIDField(blank=True, null=True, db_column='icon_file_id', help_text='板块图标文件 ID（M7 文件服务）')
    color = models.CharField(max_length=7,
        validators=[RegexValidator(regex=r'^#[0-9A-Fa-f]{6}$', message='颜色必须是 HEX 格式')],
        help_text='板块颜色（HEX 格式）')
    sort_order = models.IntegerField(default=100, validators=[MinValueValidator(1), MaxValueValidator(999)], help_text='排序号（1-999）')
    is_enabled = models.BooleanField(default=True, db_index=True, help_text='是否启用')
    posts_count = models.IntegerField(default=0, validators=[MinValueValidator(0)], help_text='板块内帖子数量')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'sections'
        managed = False
        ordering = ['sort_order', 'id']
        verbose_name = '板块'
        verbose_name_plural = '板块'

    def __str__(self):
        return f'{self.name} ({self.slug})'

    @classmethod
    def get_enabled_sections(cls):
        return cls.objects.filter(is_enabled=True).order_by('sort_order', 'id')

    @classmethod
    def get_by_slug(cls, slug):
        try:
            return cls.objects.get(slug=slug, is_enabled=True)
        except cls.DoesNotExist:
            return None

    def increment_posts_count(self, value=1):
        self.posts_count = models.F('posts_count') + value
        self.save(update_fields=['posts_count'])
        self.refresh_from_db()

    def can_be_deleted(self):
        if self.posts_count > 0:
            return False, f'板块内有 {self.posts_count} 篇帖子，无法删除'
        enabled_count = Section.objects.filter(is_enabled=True).count()
        if self.is_enabled and enabled_count <= 1:
            return False, '至少需要保留一个启用的板块'
        return True, None

    def disable(self):
        enabled_count = Section.objects.filter(is_enabled=True).count()
        if self.is_enabled and enabled_count <= 1:
            raise ValueError('至少需要保留一个启用的板块')
        self.is_enabled = False
        self.save(update_fields=['is_enabled'])

    def enable(self):
        self.is_enabled = True
        self.save(update_fields=['is_enabled'])
