# Generated by Django 3.1.7 on 2021-05-10 08:56

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0013_donation_payment_completed'),
    ]

    operations = [
        migrations.AlterField(
            model_name='causes',
            name='ngo',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='account.userprofile'),
        ),
    ]
