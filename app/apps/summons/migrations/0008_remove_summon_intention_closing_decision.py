# Generated by Django 3.1.7 on 2021-03-11 08:35

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("summons", "0007_auto_20210310_1136"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="summon",
            name="intention_closing_decision",
        ),
    ]