from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0007_remove_inventory_buying_price_and_more'),
    ]

    operations = [
        migrations.RunSQL('CREATE EXTENSION IF NOT EXISTS pg_trgm;'),
    ]
