# Generated by Django 3.1.6 on 2021-02-02 08:09

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('website', '0006_remove_otoplenie_organization'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='otoplenie',
            name='fact',
        ),
        migrations.RemoveField(
            model_name='otoplenie',
            name='limit',
        ),
        migrations.AddField(
            model_name='otoplenie',
            name='fact_apr',
            field=models.FloatField(default=0, verbose_name='Факт - апрель'),
        ),
        migrations.AddField(
            model_name='otoplenie',
            name='fact_aug',
            field=models.FloatField(default=0, verbose_name='Факт - август'),
        ),
        migrations.AddField(
            model_name='otoplenie',
            name='fact_dec',
            field=models.FloatField(default=0, verbose_name='Факт - декабрь'),
        ),
        migrations.AddField(
            model_name='otoplenie',
            name='fact_feb',
            field=models.FloatField(default=0, verbose_name='Факт - февраль'),
        ),
        migrations.AddField(
            model_name='otoplenie',
            name='fact_jan',
            field=models.FloatField(default=0, verbose_name='Факт - январь'),
        ),
        migrations.AddField(
            model_name='otoplenie',
            name='fact_jul',
            field=models.FloatField(default=0, verbose_name='Факт - июль'),
        ),
        migrations.AddField(
            model_name='otoplenie',
            name='fact_jun',
            field=models.FloatField(default=0, verbose_name='Факт - июнь'),
        ),
        migrations.AddField(
            model_name='otoplenie',
            name='fact_mar',
            field=models.FloatField(default=0, verbose_name='Факт - март'),
        ),
        migrations.AddField(
            model_name='otoplenie',
            name='fact_may',
            field=models.FloatField(default=0, verbose_name='Факт - май'),
        ),
        migrations.AddField(
            model_name='otoplenie',
            name='fact_nov',
            field=models.FloatField(default=0, verbose_name='Факт - ноябрь'),
        ),
        migrations.AddField(
            model_name='otoplenie',
            name='fact_oct',
            field=models.FloatField(default=0, verbose_name='Факт - октябрь'),
        ),
        migrations.AddField(
            model_name='otoplenie',
            name='fact_sep',
            field=models.FloatField(default=0, verbose_name='Факт - сентябрь'),
        ),
        migrations.AddField(
            model_name='otoplenie',
            name='limit_apr',
            field=models.FloatField(default=0, verbose_name='Лимит - апрель'),
        ),
        migrations.AddField(
            model_name='otoplenie',
            name='limit_aug',
            field=models.FloatField(default=0, verbose_name='Лимит - август'),
        ),
        migrations.AddField(
            model_name='otoplenie',
            name='limit_dec',
            field=models.FloatField(default=0, verbose_name='Лимит - декабрь'),
        ),
        migrations.AddField(
            model_name='otoplenie',
            name='limit_feb',
            field=models.FloatField(default=0, verbose_name='Лимит - февраль'),
        ),
        migrations.AddField(
            model_name='otoplenie',
            name='limit_jan',
            field=models.FloatField(default=0, verbose_name='Лимит - январь'),
        ),
        migrations.AddField(
            model_name='otoplenie',
            name='limit_jul',
            field=models.FloatField(default=0, verbose_name='Лимит - июль'),
        ),
        migrations.AddField(
            model_name='otoplenie',
            name='limit_jun',
            field=models.FloatField(default=0, verbose_name='Лимит - июнь'),
        ),
        migrations.AddField(
            model_name='otoplenie',
            name='limit_mar',
            field=models.FloatField(default=0, verbose_name='Лимит - март'),
        ),
        migrations.AddField(
            model_name='otoplenie',
            name='limit_may',
            field=models.FloatField(default=0, verbose_name='Лимит - май'),
        ),
        migrations.AddField(
            model_name='otoplenie',
            name='limit_nov',
            field=models.FloatField(default=0, verbose_name='Лимит - ноябрь'),
        ),
        migrations.AddField(
            model_name='otoplenie',
            name='limit_oct',
            field=models.FloatField(default=0, verbose_name='Лимит - октябрь'),
        ),
        migrations.AddField(
            model_name='otoplenie',
            name='limit_sep',
            field=models.FloatField(default=0, verbose_name='Лимит - сентябрь'),
        ),
        migrations.AddField(
            model_name='otoplenie',
            name='organization',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to='website.organization', verbose_name='Организация'),
        ),
    ]
