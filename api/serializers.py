from django.db import IntegrityError
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from rest_framework import serializers

from main.jobs import enqueue
from main.tasks import send_welcome_email_task

from chat.models import Conversation, Message
from main.models import Comment, Notification, Post, User
from main.selectors import user_counts

from .validators import validate_image_size


class UserSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'profile_pic']
        read_only_fields = fields


class UserProfileSerializer(UserSummarySerializer):
    bio = serializers.CharField(read_only=True)
    cover = serializers.ImageField(read_only=True)
    follower_count = serializers.SerializerMethodField()
    following_count = serializers.SerializerMethodField()
    is_following = serializers.SerializerMethodField()

    class Meta(UserSummarySerializer.Meta):
        fields = UserSummarySerializer.Meta.fields + ['bio', 'cover', 'follower_count', 'following_count', 'is_following']

    def get_follower_count(self, obj) -> int:
        return user_counts(obj)['followers']

    def get_following_count(self, obj) -> int:
        return user_counts(obj)['following']

    def get_is_following(self, obj) -> bool:
        viewer = self.context['request'].user
        return obj.follower_relations.filter(follower=viewer).exists()


DUPLICATE_ACCOUNT = (
    'Could not create an account with these details. If you already have one, log in or reset your password.'
)


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'first_name', 'last_name']
        extra_kwargs = {'email': {'required': True}}

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            # Same wording whether or not the address is registered, so signup cannot be used to list members' emails.
            raise serializers.ValidationError(DUPLICATE_ACCOUNT)
        return value

    def validate(self, attrs):
        candidate = User(**{key: value for key, value in attrs.items() if key != 'password'})
        try:
            validate_password(attrs['password'], candidate)
        except DjangoValidationError as error:
            raise serializers.ValidationError({'password': error.messages})
        return attrs

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        try:
            user.save()
        except IntegrityError:
            # Two signups with one address at the same moment: the database constraint decides.
            raise serializers.ValidationError({'email': [DUPLICATE_ACCOUNT]})
        enqueue(send_welcome_email_task, user.pk)
        return user


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField(write_only=True)


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


INVALID_RESET_LINK = 'This reset link is invalid or has expired. Request a new one.'


class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True, style={'input_type': 'password'})

    def validate(self, attrs):
        try:
            user = User.objects.get(pk=force_str(urlsafe_base64_decode(attrs['uid'])), is_active=True)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            raise serializers.ValidationError({'token': [INVALID_RESET_LINK]})
        # The token embeds the password hash, so it stops working as soon as the password changes.
        if not default_token_generator.check_token(user, attrs['token']):
            raise serializers.ValidationError({'token': [INVALID_RESET_LINK]})
        try:
            validate_password(attrs['new_password'], user)
        except DjangoValidationError as error:
            raise serializers.ValidationError({'new_password': error.messages})
        attrs['user'] = user
        return attrs


class CurrentUserSerializer(serializers.ModelSerializer):
    # Send remove_profile_pic / remove_cover (true) to clear a photo. A new file in the same request wins.
    remove_profile_pic = serializers.BooleanField(write_only=True, required=False, default=False)
    remove_cover = serializers.BooleanField(write_only=True, required=False, default=False)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'bio', 'profile_pic', 'cover',
            'remove_profile_pic', 'remove_cover',
        ]
        read_only_fields = ['id', 'username']
        extra_kwargs = {
            'profile_pic': {'required': False, 'validators': [validate_image_size]},
            'cover': {'required': False, 'validators': [validate_image_size]},
        }

    def validate_email(self, value):
        # An address belongs to one account. Without this check, profile edits could take another member's address.
        if value and User.objects.filter(email__iexact=value).exclude(pk=self.instance.pk).exists():
            raise serializers.ValidationError('This email address cannot be used.')
        return value

    def update(self, instance, validated_data):
        stale_files = []
        for field, flag in (('profile_pic', 'remove_profile_pic'), ('cover', 'remove_cover')):
            remove = validated_data.pop(flag, False)
            if validated_data.get(field):
                stale_files.append(getattr(instance, field).name)  # replaced by the upload
            elif remove:
                stale_files.append(getattr(instance, field).name)
                validated_data[field] = ''
        user = super().update(instance, validated_data)
        # Delete the old files only after the row no longer points at them.
        for name in stale_files:
            if name:
                user.profile_pic.storage.delete(name)
        return user


class UserSearchSerializer(UserSummarySerializer):
    is_following = serializers.BooleanField(read_only=True)

    class Meta(UserSummarySerializer.Meta):
        fields = UserSummarySerializer.Meta.fields + ['is_following']
        read_only_fields = fields


class NotificationSerializer(serializers.ModelSerializer):
    actor = UserSummarySerializer(read_only=True)
    post_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = Notification
        fields = ['id', 'verb', 'actor', 'post_id', 'created_at', 'read_at']
        read_only_fields = fields


class PostSerializer(serializers.ModelSerializer):
    author = UserSummarySerializer(source='creater', read_only=True)
    content_text = serializers.CharField(max_length=140, allow_blank=True, required=False, default='')
    content_image = serializers.ImageField(required=False, validators=[validate_image_size])
    # Lets an edit remove the photo without uploading a replacement.
    remove_image = serializers.BooleanField(write_only=True, required=False, default=False)
    is_liked = serializers.SerializerMethodField()
    is_saved = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            'id', 'author', 'content_text', 'content_image', 'content_thumbnail', 'like_count', 'comment_count',
            'is_liked', 'is_saved', 'date_created', 'remove_image',
        ]
        read_only_fields = ['content_thumbnail', 'like_count', 'comment_count', 'date_created']

    def get_is_liked(self, obj) -> bool:
        return bool(getattr(obj, 'is_liked', False))

    def get_is_saved(self, obj) -> bool:
        return bool(getattr(obj, 'is_saved', False))

    def create(self, validated_data):
        validated_data.pop('remove_image', None)  # only meaningful for edits
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data.pop('remove_image', None)
        return super().update(instance, validated_data)

    def validate(self, attrs):
        text = attrs.get('content_text', getattr(self.instance, 'content_text', ''))
        image = attrs.get('content_image', getattr(self.instance, 'content_image', None))
        if attrs.get('remove_image') and 'content_image' not in attrs:
            image = None
        if not (text or image):
            raise serializers.ValidationError('A post needs text or an image.')
        return attrs


class CommentSerializer(serializers.ModelSerializer):
    author = UserSummarySerializer(source='commenter', read_only=True)
    body = serializers.CharField(source='comment_content', max_length=90)
    parent = serializers.PrimaryKeyRelatedField(queryset=Comment.objects.all(), required=False, allow_null=True, write_only=True)
    parent_id = serializers.IntegerField(read_only=True)
    reply_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'author', 'body', 'comment_time', 'parent', 'parent_id', 'reply_count']
        read_only_fields = ['comment_time']


class MessageSerializer(serializers.ModelSerializer):
    sender = UserSummarySerializer(read_only=True)
    body = serializers.CharField(max_length=1000)

    class Meta:
        model = Message
        fields = ['id', 'sender', 'body', 'created_at']
        read_only_fields = ['created_at']


class ConversationSerializer(serializers.ModelSerializer):
    other_user = serializers.SerializerMethodField()
    unread_count = serializers.IntegerField(read_only=True)
    other_last_read_at = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = ['id', 'other_user', 'unread_count', 'other_last_read_at']

    def _other_membership(self, obj):
        viewer_id = self.context['request'].user.id
        for membership in obj.memberships.all():  # prefetched by the view
            if membership.user_id != viewer_id:
                return membership
        return None

    def get_other_user(self, obj) -> dict | None:
        membership = self._other_membership(obj)
        return UserSummarySerializer(membership.user, context=self.context).data if membership else None

    def get_other_last_read_at(self, obj) -> str | None:
        membership = self._other_membership(obj)
        return membership.last_read_at.isoformat() if membership and membership.last_read_at else None
