# Generated by Django 3.1.6 on 2021-02-11 08:30

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('website', '0009_auto_20210211_1525'),
    ]

    operations = [
        migrations.AddField(
            model_name='adress',
            name='organization',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to='website.organization', verbose_name='Организация'),
        ),
    ]