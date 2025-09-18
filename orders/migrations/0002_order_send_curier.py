from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='send_curier',
            field=models.BooleanField(default=False, help_text='Indicates whether order has been sent to courier service'),
        ),
    ]