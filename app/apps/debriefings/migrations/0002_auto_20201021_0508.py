# Generated by Django 3.1.2 on 2020-10-21 05:08

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("debriefings", "0001_initial"),
    ]

    operations = [
        migrations.RenameField(
            model_name="debrief",
            old_name="user",
            new_name="author",
        ),
    ]