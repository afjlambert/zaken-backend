# Generated by Django 3.1.7 on 2021-03-10 09:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("summons", "0004_auto_20210207_1956"),
    ]

    operations = [
        migrations.AddField(
            model_name="summontype",
            name="camunda_option",
            field=models.CharField(default="aanschrijvingen", max_length=255),
        ),
    ]