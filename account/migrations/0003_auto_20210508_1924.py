# Generated by Django 3.1.7 on 2021-05-08 13:39

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0002_causes_donation'),
    ]

    operations = [
        migrations.RenameField(
            model_name='userprofile',
            old_name='shopname',
            new_name='ngoname',
        ),
    ]