# Generated by Django 3.1.5 on 2021-01-21 14:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("cases", "0027_auto_20210120_1346"),
    ]

    operations = [
        migrations.AddField(
            model_name="case",
            name="text",
            field=models.TextField(blank=True, null=True),
        ),
    ]
