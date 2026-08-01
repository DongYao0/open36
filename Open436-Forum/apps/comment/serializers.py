"""
Comment serializers
"""
from rest_framework import serializers
from .models import Reply, PostLike, PostFavorite, ReplyLike


class ReplyListSerializer(serializers.ModelSerializer):
    """回复列表序列化器"""
    author = serializers.SerializerMethodField()
    is_edited = serializers.SerializerMethodField()
    can_edit = serializers.SerializerMethodField()
    can_delete = serializers.SerializerMethodField()
    likes_count = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()

    class Meta:
        model = Reply
        fields = [
            'id', 'post_id', 'parent_id', 'author', 'content', 'floor_number',
            'is_deleted', 'edit_count', 'last_edited_at',
            'is_edited', 'can_edit', 'can_delete', 'likes_count', 'is_liked',
            'created_at', 'updated_at',
        ]

    def get_author(self, obj):
        return {'user_id': obj.author_id, 'nickname': None, 'avatar_url': None}

    def get_is_edited(self, obj):
        return obj.edit_count > 0

    def get_can_edit(self, obj):
        request = self.context.get('request')
        if not request:
            return False
        return obj.can_edit(getattr(request, 'user_id', None), getattr(request, 'is_admin', False))

    def get_can_delete(self, obj):
        request = self.context.get('request')
        if not request:
            return False
        if getattr(request, 'is_admin', False):
            return True
        return obj.author_id == getattr(request, 'user_id', None)

    def get_likes_count(self, obj):
        return ReplyLike.objects.filter(reply_id=obj.id).count()

    def get_is_liked(self, obj):
        request = self.context.get('request')
        if not request:
            return False
        user_id = getattr(request, 'user_id', None)
        if not user_id:
            return False
        return ReplyLike.objects.filter(reply_id=obj.id, user_id=user_id).exists()


class ReplyCreateSerializer(serializers.ModelSerializer):
    """创建回复序列化器"""
    content = serializers.CharField()
    parent_id = serializers.IntegerField(required=False, allow_null=True, default=None)

    class Meta:
        model = Reply
        fields = ['content', 'parent_id']

    def validate_content(self, value):
        value = value.strip()
        if len(value) < 2:
            raise serializers.ValidationError('回复内容至少2个字符')
        if len(value) > 10000:
            raise serializers.ValidationError('回复内容不能超过10000个字符')
        return value


class ReplyUpdateSerializer(serializers.ModelSerializer):
    """更新回复序列化器"""
    content = serializers.CharField()

    class Meta:
        model = Reply
        fields = ['content']

    def validate_content(self, value):
        value = value.strip()
        if len(value) < 2:
            raise serializers.ValidationError('回复内容至少2个字符')
        if len(value) > 10000:
            raise serializers.ValidationError('回复内容不能超过10000个字符')
        return value


class PostLikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostLike
        fields = ['id', 'post_id', 'user_id', 'created_at']


class PostFavoriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostFavorite
        fields = ['id', 'post_id', 'user_id', 'created_at']


class FavoriteListSerializer(serializers.ModelSerializer):
    post = serializers.SerializerMethodField()

    class Meta:
        model = PostFavorite
        fields = ['id', 'post', 'created_at']

    def get_post(self, obj):
        return {'post_id': obj.post_id, 'title': None, 'author': None, 'created_at': None}
