# Generated by Django 2.1.15 on 2021-03-07 07:20

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_auto_20210307_0711'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='account',
            unique_together={('integration', 'user')},
        ),
    ]
