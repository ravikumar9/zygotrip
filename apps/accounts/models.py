from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from apps.core.models import TimeStampedModel


class UserManager(BaseUserManager):
	def create_user(self, email, password=None, **extra_fields):
		if not email:
			raise ValueError('Email is required')
		email = self.normalize_email(email)
		user = self.model(email=email, **extra_fields)
		user.set_password(password)
		user.save(using=self._db)
		return user

	def create_superuser(self, email, password=None, **extra_fields):
		extra_fields.setdefault('is_staff', True)
		extra_fields.setdefault('is_superuser', True)
		extra_fields.setdefault('is_active', True)
		return self.create_user(email, password, **extra_fields)


class User(TimeStampedModel, AbstractBaseUser, PermissionsMixin):
	email = models.EmailField(unique=True)
	full_name = models.CharField(max_length=120)
	phone = models.CharField(max_length=20, blank=True)
	is_staff = models.BooleanField(default=False)
	roles = models.ManyToManyField('Role', through='UserRole', related_name='users')

	objects = UserManager()

	USERNAME_FIELD = 'email'
	REQUIRED_FIELDS = ['full_name']

	def __str__(self):
		return self.email


class Role(TimeStampedModel):
	code = models.CharField(max_length=50, unique=True)
	name = models.CharField(max_length=80)
	description = models.TextField(blank=True)
	permissions = models.ManyToManyField('Permission', through='RolePermission', related_name='roles')

	def __str__(self):
		return self.name


class Permission(TimeStampedModel):
	code = models.CharField(max_length=80, unique=True)
	name = models.CharField(max_length=120)
	description = models.TextField(blank=True)

	def __str__(self):
		return self.code


class RolePermission(TimeStampedModel):
	role = models.ForeignKey(Role, on_delete=models.CASCADE)
	permission = models.ForeignKey(Permission, on_delete=models.CASCADE)

	class Meta:
		unique_together = ('role', 'permission')


class UserRole(TimeStampedModel):
	user = models.ForeignKey(User, on_delete=models.CASCADE)
	role = models.ForeignKey(Role, on_delete=models.CASCADE)

	class Meta:
		unique_together = ('user', 'role')

# Create your models here.