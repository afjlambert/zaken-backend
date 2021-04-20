# Generated by Django 3.1.7 on 2021-04-15 07:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("camunda", "0005_auto_20210406_1528"),
    ]

    operations = [
        migrations.CreateModel(
            name="CamundaProcess",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=255)),
                ("camunda_process_name", models.CharField(max_length=255)),
            ],
            options={
                "ordering": ["-name"],
            },
        ),
    ]