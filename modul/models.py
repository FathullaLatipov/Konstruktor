import random
from datetime import datetime

from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import AbstractUser, PermissionsMixin
from django.db import models
from django.utils import timezone
from pytz import utc


class CustomUserManager(BaseUserManager):
    def create_user(self, uid, username=None, first_name=None, last_name=None, profile_image=None, password=None,
                    **extra_fields):
        """
        Создает и сохраняет обычного пользователя с указанным UID.
        """
        if not uid:
            raise ValueError('Пользователь должен иметь UID')

        user = self.model(uid=uid, username=username, first_name=first_name, last_name=last_name,
                          profile_image=profile_image, **extra_fields)

        # Если пароль предоставлен, установите его, иначе оставьте None (или установите неиспользуемый пароль)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()

        user.save(using=self._db)
        return user

    def create_superuser(self, uid, username=None, first_name=None, last_name=None, profile_image=None, password=None,
                         **extra_fields):
        """
        Создает и сохраняет суперпользователя с указанным UID.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Суперпользователь должен иметь is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Суперпользователь должен иметь is_superuser=True.')

        return self.create_user(uid, username, first_name, last_name, profile_image, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    uid = models.BigIntegerField(unique=True, null=True, default=random.randint(1000000000, 9999999999))
    username = models.CharField(max_length=255, null=True, blank=True, unique=True)
    first_name = models.CharField(max_length=255, null=True, blank=True)
    last_name = models.CharField(max_length=255, null=True, blank=True)
    profile_image = models.FileField(upload_to='images', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    USERNAME_FIELD = 'uid'  # Поле, которое используется для входа в систему
    REQUIRED_FIELDS = []  # Список полей, необходимых для создания суперпользователя
    objects = CustomUserManager()

    def __str__(self):
        return self.username or f'User {self.uid}'

    class Meta:
        verbose_name = 'user'
        verbose_name_plural = 'users'

class Bot(models.Model):
    token = models.CharField(max_length=255, unique=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="bots")
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name="child_bots")
    bot_enable = models.BooleanField(default=True)
    username = models.CharField(max_length=255)
    unauthorized = models.BooleanField(default=False)
    photo = models.CharField(max_length=255, null=True, blank=True)
    photo_is_gif = models.BooleanField(default=False)
    news_channel = models.CharField(max_length=255, null=True, blank=True)
    support = models.CharField(max_length=32, null=True, blank=True)
    mandatory_subscription = models.BooleanField(default=False)
    enable_promotion = models.BooleanField(default=False)
    enable_child_bot = models.BooleanField(default=False)
    enable_music = models.BooleanField(default=False)
    enable_download = models.BooleanField(default=False)
    enable_leo = models.BooleanField(default=False)
    enable_chatgpt = models.BooleanField(default=False)
    enable_horoscope = models.BooleanField(default=False)
    enable_anon = models.BooleanField(default=False)
    enable_sms = models.BooleanField(default=False)

    def __str__(self):
        return self.username


class UserTG(models.Model):
    uid = models.BigIntegerField(unique=True)
    username = models.CharField(max_length=255, null=True, blank=True)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255, null=True, blank=True)
    last_interaction = models.DateTimeField(null=True, blank=True, default=datetime.now(tz=utc))
    interaction_count = models.IntegerField(null=True, blank=True, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.username or f'User {self.uid}'


class ClientBotUser(models.Model):
    user = models.ForeignKey(UserTG, on_delete=models.CASCADE, related_name="client_bot_users")
    bot = models.ForeignKey(Bot, on_delete=models.CASCADE, related_name="clients")
    uid = models.BigIntegerField()
    balance = models.FloatField(default=0)
    referral_count = models.IntegerField(default=0)
    referral_balance = models.FloatField(default=0)
    inviter = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='referrals')
    inviter_got_bonus = models.BooleanField(default=False)
    subscribed_all_chats = models.BooleanField(default=False)
    subscribed_chats_at = models.DateTimeField(default=datetime(1970, 1, 1, tzinfo=utc))
    current_ai_limit = models.IntegerField(default=12)
    enable_horoscope_everyday_alert = models.BooleanField(default=False)

    def __str__(self):
        return f'ClientBotUser {self.uid}'




# Enums
class SexEnum(models.TextChoices):
    MALE = "MALE", "Male"
    FEMALE = "FEMALE", "Female"
    ANY = "ANY", "Any"


class MediaTypeEnum(models.TextChoices):
    PHOTO = "PHOTO", "Photo"
    VIDEO = "VIDEO", "Video"
    VIDEO_NOTE = "VIDEO_NOTE", "Video Note"


class GPTTypeEnum(models.TextChoices):
    REQUEST = "REQUEST", "Request"
    PICTURE = "PICTURE", "Picture"
    TEXT_TO_SPEECH = "TEXT_TO_SPEECH", "Text to Speech"
    SPEECH_TO_TEXT = "SPEECH_TO_TEXT", "Speech to Text"
    ASSISTANT = "ASSISTANT", "Assistant"


class TaskTypeEnum(models.TextChoices):
    DOWNLOAD_MEDIA = "DOWNLOAD_MEDIA", "Download Media"


class BroadcastTypeEnum(models.TextChoices):
    TEXT = "TEXT", "Text"
    PHOTO = "PHOTO", "Photo"
    VIDEO = "VIDEO", "Video"
    VIDEO_NOTE = "VIDEO_NOTE", "Video Note"
    AUDIO = "AUDIO", "Audio"


# Models
class DownloadAnalyticsModel(models.Model):
    bot_username = models.CharField(max_length=100)
    domain = models.CharField(max_length=1024)
    count = models.IntegerField(default=0)
    date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.bot_username} - {self.domain} - {self.count}"

#
# class User(models.Model):
#     username = models.CharField(max_length=255)
#
#     # Добавьте другие поля по необходимости
#
#     def __str__(self):
#         return self.username


class LeoMatchModel(models.Model):
    user = models.ForeignKey(UserTG, on_delete=models.CASCADE)
    photo = models.CharField(max_length=1024)
    media_type = models.CharField(max_length=50, choices=MediaTypeEnum.choices)
    sex = models.CharField(max_length=50, choices=SexEnum.choices)
    age = models.IntegerField()
    full_name = models.CharField(max_length=15)
    about_me = models.CharField(max_length=300)
    city = models.CharField(max_length=50)
    which_search = models.CharField(max_length=50, choices=SexEnum.choices)
    search = models.BooleanField(default=True)
    active = models.BooleanField(default=True)
    bot_username = models.CharField(max_length=100)
    count_likes = models.IntegerField(default=0)
    blocked = models.BooleanField(default=False)

    def __str__(self):
        return self.full_name


class LeoMatchLikesBasketModel(models.Model):
    from_user = models.ForeignKey(LeoMatchModel, related_name="leo_match_from_user", on_delete=models.CASCADE)
    to_user = models.ForeignKey(LeoMatchModel, related_name="leo_match_to_user", on_delete=models.CASCADE)
    message = models.CharField(max_length=1024, null=True)
    done = models.BooleanField(default=False)

    def __str__(self):
        return f"From {self.from_user} to {self.to_user}"


class GPTRecordModel(models.Model):
    user = models.ForeignKey(UserTG, on_delete=models.CASCADE)
    bot = models.ForeignKey(User, related_name="bot_user", on_delete=models.CASCADE)  # Assuming Bot is another User
    message = models.CharField(max_length=1024)
    type = models.CharField(max_length=50, choices=GPTTypeEnum.choices)

    def __str__(self):
        return f"{self.type} - {self.message}"


class TaskModel(models.Model):
    client = models.ForeignKey(UserTG, on_delete=models.CASCADE)
    task_type = models.CharField(max_length=50, choices=TaskTypeEnum.choices)
    data = models.JSONField()

    def __str__(self):
        return f"{self.task_type} for {self.client}"


class AnonClientModel(models.Model):
    user = models.ForeignKey(UserTG, on_delete=models.CASCADE)
    sex = models.CharField(max_length=50, choices=SexEnum.choices)
    status = models.IntegerField(default=0)
    vip_date_end = models.DateTimeField(null=True)
    job_id = models.CharField(max_length=255, null=True)
    bot_username = models.CharField(max_length=100, default="")

    def __str__(self):
        return f"Anon Client {self.user}"


class AnonChatModel(models.Model):
    user = models.ForeignKey(AnonClientModel, related_name="anon_chat_user", on_delete=models.CASCADE)
    partner = models.ForeignKey(AnonClientModel, related_name="anon_chat_partner", on_delete=models.CASCADE)

    def __str__(self):
        return f"Chat between {self.user} and {self.partner}"


class SMSBanModel(models.Model):
    user = models.ForeignKey(UserTG, on_delete=models.CASCADE)
    service = models.CharField(max_length=100)
    phone = models.CharField(max_length=50)

    def __str__(self):
        return f"SMS Ban {self.service} for {self.user}"


class SMSOrder(models.Model):
    user = models.ForeignKey(UserTG, on_delete=models.CASCADE)
    order_id = models.BigIntegerField(unique=True)
    country_code = models.CharField(max_length=20, default="")
    product = models.CharField(max_length=255)
    phone = models.CharField(max_length=255)
    receive_code = models.CharField(max_length=255, default="")
    receive_status = models.CharField(max_length=10, default="wait")
    price = models.FloatField()
    order_created_at = models.DateTimeField(auto_now=True)
    profit = models.FloatField(default=0)
    bot_admin_profit = models.FloatField(default=0)
    msg_id = models.BigIntegerField(null=True)

    def __str__(self):
        return f"SMS Order {self.order_id} for {self.user}"
