# Generated by Django 4.2 on 2024-06-20 19:28

import datetime
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import phonenumber_field.modelfields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Competitor',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('registration_date', models.DateField(auto_now_add=True)),
                ('hcp', models.DecimalField(decimal_places=1, max_digits=3, validators=[django.core.validators.MinValueValidator(0.0), django.core.validators.MaxValueValidator(54.0)])),
                ('competitor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='accounts.userprofile')),
            ],
        ),
        migrations.CreateModel(
            name='GolfCourse',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=100)),
                ('contact_person', models.CharField(max_length=100)),
                ('telephone', phonenumber_field.modelfields.PhoneNumberField(max_length=128, region=None)),
                ('email', models.EmailField(max_length=100)),
                ('address', models.CharField(max_length=100)),
                ('zip_code', models.IntegerField(validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(99999)])),
                ('city', models.CharField(max_length=100)),
                ('country', models.CharField(choices=[('DE', 'Germany'), ('EN', 'England'), ('FR', 'France')], default='DE', max_length=2)),
                ('greenfee_external', models.DecimalField(decimal_places=1, default=0, max_digits=4)),
                ('greenfee_member', models.DecimalField(decimal_places=1, default=0, max_digits=4)),
            ],
        ),
        migrations.CreateModel(
            name='Tournament',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('slug', models.SlugField(blank=True, null=True, unique=True)),
                ('creation_date', models.DateField(auto_now_add=True)),
                ('updated_date', models.DateTimeField(auto_now=True)),
                ('date', models.DateField(default=django.utils.timezone.now)),
                ('tee_time', models.TimeField(blank=True, default=datetime.time(9, 0), null=True)),
                ('hcp_limit', models.DecimalField(decimal_places=1, max_digits=3, validators=[django.core.validators.MinValueValidator(0.0), django.core.validators.MaxValueValidator(54.0)])),
                ('hcp_relevant', models.BooleanField(default=True)),
                ('max_participants', models.IntegerField(default=30)),
                ('comment', models.TextField(blank=True)),
                ('course', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='tournaments.golfcourse')),
                ('participants', models.ManyToManyField(blank=True, related_name='competitors', through='tournaments.Competitor', to='accounts.userprofile')),
                ('supervisor', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='supervising_tournament', to='accounts.userprofile')),
            ],
        ),
        migrations.AddField(
            model_name='competitor',
            name='tournament',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='tournaments.tournament'),
        ),
    ]
