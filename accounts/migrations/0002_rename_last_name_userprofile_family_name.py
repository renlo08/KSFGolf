# Generated by Django 4.2 on 2024-06-03 17:47

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='userprofile',
            old_name='last_name',
            new_name='family_name',
        ),
    ]
