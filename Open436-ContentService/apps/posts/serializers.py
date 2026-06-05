"""
Post serializers
"""
from rest_framework import serializers
from .models import Post, PostEditHistory


class PostListSerializer(serializers.ModelSerializer):
    """帖子列表序列化器（精简）"""

    author = serializers.SerializerMethodField()
    section = serializers.SerializerMethodField()
    content_preview = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            'id', 'title', 'content_preview', 'author', 'section',
            'is_pinned', 'pin_type', 'views_count', 'replies_count', 'likes_count',
            'status', 'created_at', 'updated_at',
        ]

    def get_author(self, obj):
        return {
            'user_id': obj.author_id,
            'nickname': None,
            'avatar_url': None,
        }

    def get_section(self, obj):
        return {
            'section_id': obj.section_id,
            'name': None,
        }

    def get_content_preview(self, obj):
        import re
        text = re.sub(r'<[^>]+>', '', obj.content)
        return text[:200] + ('...' if len(text) > 200 else '')


class PostDetailSerializer(serializers.ModelSerializer):
    """帖子详情序列化器"""

    author = serializers.SerializerMethodField()
    section = serializers.SerializerMethodField()
    is_edited = serializers.SerializerMethodField()
    can_edit = serializers.SerializerMethodField()
    can_delete = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            'id', 'title', 'content', 'author', 'section',
            'is_pinned', 'pin_type', 'views_count',
            'replies_count', 'likes_count',
            'status', 'edit_count', 'last_edited_at', 'last_edited_by',
            'is_edited', 'can_edit', 'can_delete',
            'created_at', 'updated_at',
        ]

    def get_author(self, obj):
        return {
            'user_id': obj.author_id,
            'nickname': None,
            'avatar_url': None,
        }

    def get_section(self, obj):
        return {
            'section_id': obj.section_id,
            'name': None,
        }

    def get_is_edited(self, obj):
        return obj.edit_count > 0

    def get_can_edit(self, obj):
        request = self.context.get('request')
        if not request:
            return False
        return obj.can_edit(
            getattr(request, 'user_id', None),
            getattr(request, 'is_admin', False)
        )

    def get_can_delete(self, obj):
        request = self.context.get('request')
        if not request:
            return False
        if getattr(request, 'is_admin', False):
            return True
        return obj.author_id == getattr(request, 'user_id', None)


class PostCreateSerializer(serializers.ModelSerializer):
    """创建帖子序列化器"""

    title = serializers.CharField(max_length=100)
    content = serializers.CharField()
    section_id = serializers.IntegerField()

    class Meta:
        model = Post
        fields = ['title', 'content', 'section_id']

    def validate_title(self, value):
        value = value.strip()
        if len(value) < 5:
            raise serializers.ValidationError('标题长度至少5个字符')
        if len(value) > 100:
            raise serializers.ValidationError('标题长度不能超过100个字符')
        return value

    def validate_content(self, value):
        value = value.strip()
        if len(value) < 10:
            raise serializers.ValidationError('内容长度至少10个字符')
        if len(value) > 50000:
            raise serializers.ValidationError('内容长度不能超过50000个字符')
        return value


class PostUpdateSerializer(serializers.ModelSerializer):
    """更新帖子序列化器"""

    title = serializers.CharField(required=False, max_length=100)
    content = serializers.CharField(required=False)
    section_id = serializers.IntegerField(required=False)

    class Meta:
        model = Post
        fields = ['title', 'content', 'section_id']

    def validate_title(self, value):
        value = value.strip()
        if len(value) < 5:
            raise serializers.ValidationError('标题长度至少5个字符')
        if len(value) > 100:
            raise serializers.ValidationError('标题长度不能超过100个字符')
        return value

    def validate_content(self, value):
        value = value.strip()
        if len(value) < 10:
            raise serializers.ValidationError('内容长度至少10个字符')
        if len(value) > 50000:
            raise serializers.ValidationError('内容长度不能超过50000个字符')
        return value


class PostEditHistorySerializer(serializers.ModelSerializer):
    """编辑历史序列化器"""

    class Meta:
        model = PostEditHistory
        fields = ['id', 'title', 'content', 'section_id', 'edited_by', 'created_at']
