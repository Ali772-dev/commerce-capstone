# Generated for Auction end_time field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auctions', '0009_remove_listing_current_bid_alter_listing_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='listing',
            name='end_time',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
