# Generated by Django 3.1.6 on 2021-02-11 11:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('website', '0003_otoplenie_otklonenie_percent'),
    ]

    operations = [
        migrations.AlterField(
            model_name='otoplenie',
            name='otklonenie_percent',
            field=models.FloatField(editable=False, max_length=30),
        ),
    ]