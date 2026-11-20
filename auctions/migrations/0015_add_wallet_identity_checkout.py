from decimal import Decimal
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auctions', '0014_alter_notification_notification_type_report'),
    ]

    operations = [
        # 1. User Identity & Location fields
        migrations.AddField(
            model_name='user',
            name='fin_code',
            field=models.CharField(blank=True, max_length=7, null=True, verbose_name='FİN kod'),
        ),
        migrations.AddField(
            model_name='user',
            name='id_card_number',
            field=models.CharField(blank=True, max_length=20, null=True, verbose_name='Ş/V seriya və nömrəsi'),
        ),
        migrations.AddField(
            model_name='user',
            name='birth_date',
            field=models.DateField(blank=True, null=True, verbose_name='Doğum tarixi'),
        ),
        migrations.AddField(
            model_name='user',
            name='city',
            field=models.CharField(blank=True, max_length=64, null=True, verbose_name='Şəhər / Rayon'),
        ),
        migrations.AddField(
            model_name='user',
            name='address',
            field=models.TextField(blank=True, null=True, verbose_name='Dəqiq çatdırılma ünvanı'),
        ),
        migrations.AddField(
            model_name='user',
            name='postal_code',
            field=models.CharField(blank=True, max_length=10, null=True, verbose_name='Poçt indeksi'),
        ),

        # 2. AuctionResult payment & delivery fields
        migrations.AddField(
            model_name='auctionresult',
            name='payment_status',
            field=models.CharField(choices=[('PENDING', 'Ödəniş Gözlənilir'), ('PAID', 'Ödənildi'), ('CANCELLED', 'İmtina Edildi / Ödənilmədi')], default='PENDING', max_length=20, verbose_name='Ödəniş statusu'),
        ),
        migrations.AddField(
            model_name='auctionresult',
            name='paid_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Ödəniş vaxtı'),
        ),
        migrations.AddField(
            model_name='auctionresult',
            name='delivery_city',
            field=models.CharField(blank=True, max_length=64, null=True, verbose_name='Çatdırılma şəhəri'),
        ),
        migrations.AddField(
            model_name='auctionresult',
            name='delivery_address',
            field=models.TextField(blank=True, null=True, verbose_name='Çatdırılma ünvanı'),
        ),
        migrations.AddField(
            model_name='auctionresult',
            name='delivery_phone',
            field=models.CharField(blank=True, max_length=20, null=True, verbose_name='Əlaqə nömrəsi'),
        ),
        migrations.AddField(
            model_name='auctionresult',
            name='delivery_notes',
            field=models.TextField(blank=True, null=True, verbose_name='Kuryer qeydi'),
        ),

        # 3. Notification choices update
        migrations.AlterField(
            model_name='notification',
            name='notification_type',
            field=models.CharField(choices=[('won', 'Qalibiyyət Bildirişi (WON)'), ('lost', 'Məğlubiyyət Bildirişi (LOST)'), ('bid', 'Yeni Təklif'), ('outbid', 'Təklif Keçildi'), ('payment', 'Ödəniş / Cüzdan Bildirişi'), ('delivery', 'Çatdırılma / Sifariş Bildirişi'), ('comment', 'Şərh'), ('follow', 'İzləmə'), ('closed', 'Hərrac Bağlandı'), ('report', 'Xəta / Şikayət Bildirişi')], default='comment', max_length=32),
        ),

        # 4. WalletTransaction model
        migrations.CreateModel(
            name='WalletTransaction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('transaction_type', models.CharField(choices=[('DEPOSIT', 'Balans Artırılması'), ('WITHDRAW', 'Balansdan Çıxarış'), ('AUCTION_PAYMENT', 'Hərrac Ödənişi'), ('AUCTION_EARNINGS', 'Satış Gəliri'), ('PENALTY', 'Cərimə / Etibarsızlıq Tutulması'), ('REFUND', 'Geri Qaytarılma')], max_length=32, verbose_name='Əməliyyat növü')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=12, verbose_name='Məbləğ (₼)')),
                ('balance_after', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=12, verbose_name='Əməliyyatdan sonrakı balans')),
                ('status', models.CharField(choices=[('SUCCESS', 'Uğurlu'), ('PENDING', 'Gözlənilir'), ('FAILED', 'Uğursuz')], default='SUCCESS', max_length=20, verbose_name='Status')),
                ('description', models.CharField(blank=True, max_length=255, null=True, verbose_name='Təsvir')),
                ('card_last_four', models.CharField(blank=True, max_length=4, null=True, verbose_name='Kartın son 4 rəqəmi')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Tarix')),
                ('listing', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='transactions', to='auctions.listing', verbose_name='Əlaqəli elan')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='wallet_transactions', to=settings.AUTH_USER_MODEL, verbose_name='İstifadəçi')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]
