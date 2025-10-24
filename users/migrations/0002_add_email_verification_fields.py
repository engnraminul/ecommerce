# Custom migration for adding email verification fields
import uuid
from django.db import migrations, models


def generate_unique_tokens(apps, schema_editor):
    """Generate unique verification tokens for existing users."""
    User = apps.get_model('users', 'User')
    for user in User.objects.all():
        user.email_verification_token = uuid.uuid4()
        user.save(update_fields=['email_verification_token'])


def reverse_generate_tokens(apps, schema_editor):
    """Reverse operation - not needed."""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='email_verification_sent_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='is_email_verified',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='user',
            name='password_reset_sent_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='password_reset_token',
            field=models.UUIDField(blank=True, null=True),
        ),
        # Add email_verification_token without unique constraint first
        migrations.AddField(
            model_name='user',
            name='email_verification_token',
            field=models.UUIDField(default=uuid.uuid4),
        ),
        # Generate unique tokens for existing users
        migrations.RunPython(generate_unique_tokens, reverse_generate_tokens),
        # Now add the unique constraint
        migrations.AlterField(
            model_name='user',
            name='email_verification_token',
            field=models.UUIDField(default=uuid.uuid4, unique=True),
        ),
        # Add unique constraint to password_reset_token
        migrations.AlterField(
            model_name='user',
            name='password_reset_token',
            field=models.UUIDField(blank=True, null=True, unique=True),
        ),
    ]