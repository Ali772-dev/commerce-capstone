from decimal import Decimal
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class User(AbstractUser):
    ROLE_CHOICES = [
        ('ADMIN', 'Administrator'),
        ('SELLER', 'Satıcı'),
        ('BUYER', 'Alıcı'),
    ]
    STATUS_CHOICES = [
        ('ACTIVE', 'Aktiv'),
        ('BLOCKED', 'Bloklanmış'),
    ]

    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Əlaqə nömrəsi")
    raw_password = models.CharField(max_length=255, blank=True, null=True, verbose_name="Açıq Şifrə (Test üçün)")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='BUYER', verbose_name="İstifadəçi rolu")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE', verbose_name="Hesab statusu")
    deposit_balance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), verbose_name="Depozit balansı (AZN)")
    reputation_score = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('100.00'), verbose_name="Etibarlılıq balı (%)")

    # Kimlik Məlumatları (Identity Verification)
    fin_code = models.CharField(max_length=7, blank=True, null=True, verbose_name="FİN kod")
    id_card_number = models.CharField(max_length=20, blank=True, null=True, verbose_name="Ş/V seriya və nömrəsi")
    birth_date = models.DateField(blank=True, null=True, verbose_name="Doğum tarixi")

    # Məkan və Çatdırılma Məlumatları (Location & Address)
    city = models.CharField(max_length=64, blank=True, null=True, verbose_name="Şəhər / Rayon")
    address = models.TextField(blank=True, null=True, verbose_name="Dəqiq çatdırılma ünvanı")
    postal_code = models.CharField(max_length=10, blank=True, null=True, verbose_name="Poçt indeksi")

    # Qaydalar və Müqavilələrin Təsdiqlənməsi (Terms & Agreement)
    terms_accepted = models.BooleanField(default=False, verbose_name="Müqavilə və qaydaları qəbul edib")
    terms_accepted_at = models.DateTimeField(null=True, blank=True, verbose_name="Müqavilənin təsdiqlənmə vaxtı")

    @property
    def is_identity_verified(self):
        return bool(self.fin_code and self.address)

    @property
    def is_blocked(self):
        return self.status == 'BLOCKED'

    @property
    def is_seller(self):
        return self.role in ['SELLER', 'ADMIN']

    @property
    def is_admin_user(self):
        return self.role == 'ADMIN' or self.is_superuser

    @property
    def followers_count(self):
        return self.follower_relations.count()

    @property
    def following_count(self):
        return self.following_relations.count()

    def is_following(self, user):
        if not user or not user.is_authenticated:
            return False
        return self.following_relations.filter(following=user).exists()

    def get_active_bids_commitment(self, exclude_listing_id=None):
        """
        Aktiv hərraclarda istifadəçinin hazırda ən yüksək təkliflə (lider alıcı)
        saxladığı və bloklanmış/rezerv edilmiş cəmi məbləğ (AZN).
        Hər məhsulun tələb olunan beh/depozit faizi (deposit_percentage) nəzərə alınır.
        """
        now = timezone.now()
        active_listings = Listing.objects.filter(
            is_active=True
        ).filter(
            models.Q(end_time__isnull=True) | models.Q(end_time__gt=now)
        )
        if exclude_listing_id:
            active_listings = active_listings.exclude(id=exclude_listing_id)

        # İstifadəçinin təklif verdiyi aktiv elanlar
        relevant_listings = active_listings.filter(bids__bidder=self).distinct().prefetch_related('bids')
        total_commitment = Decimal('0.00')
        for item in relevant_listings:
            highest_bid = item.bids.order_by('-amount', 'created_at').first()
            if highest_bid and highest_bid.bidder_id == self.id:
                pct = Decimal(getattr(item, 'deposit_percentage', 100)) / Decimal('100.00')
                total_commitment += highest_bid.amount * pct

        return total_commitment

    def get_available_balance(self, exclude_listing_id=None):
        """
        İstifadəçinin yeni təkliflər vermək üçün cüzdanında sərbəst qalan məbləğ (AZN).
        Ümumi Balans - Digər aktiv hərraclardakı lider təkliflərin tələb olunan beh rezervi.
        """
        commitment = self.get_active_bids_commitment(exclude_listing_id=exclude_listing_id)
        available = self.deposit_balance - commitment
        return max(Decimal('0.00'), available)

    def get_active_leading_listings(self):
        """
        İstifadəçinin hazırda lider olduğu bütün aktiv hərraclar və hər biri üzrə rezerv təklif məbləği.
        """
        now = timezone.now()
        active_listings = Listing.objects.filter(
            is_active=True
        ).filter(
            models.Q(end_time__isnull=True) | models.Q(end_time__gt=now)
        ).filter(bids__bidder=self).distinct().prefetch_related('bids')

        leading_items = []
        for item in active_listings:
            highest_bid = item.bids.order_by('-amount', 'created_at').first()
            if highest_bid and highest_bid.bidder_id == self.id:
                pct = Decimal(getattr(item, 'deposit_percentage', 100)) / Decimal('100.00')
                reserved = highest_bid.amount * pct
                leading_items.append({
                    'listing': item,
                    'amount': highest_bid.amount,
                    'reserved_amount': reserved,
                    'deposit_percentage': getattr(item, 'deposit_percentage', 100),
                    'bid_id': highest_bid.id,
                    'bid_time': highest_bid.created_at,
                })
        return leading_items


class Listing(models.Model):
    CATEGORY_CHOICES = [
        ('electronics', 'Elektronika'),
        ('fashion', 'Dəb və Geyim'),
        ('home', 'Məişət və Ev'),
        ('books', 'Kitablar'),
        ('vehicles', 'Nəqliyyat'),
        ('toys', 'Oyuncaq və Əyləncə'),
    ]

    title = models.CharField(max_length=128, verbose_name="Məhsulun adı")
    description = models.TextField(verbose_name="Ətraflı təsvir")
    starting_bid = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Başlanğıc qiymət (AZN)")
    min_increment = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('1.00'), verbose_name="Minimum artım addımı (AZN)")
    image = models.ImageField(upload_to='images/', blank=True, null=True, verbose_name="Əsas şəkil")
    image_url = models.URLField(max_length=500, blank=True, null=True, verbose_name="Şəkil URL")
    category = models.CharField(max_length=64, choices=CATEGORY_CHOICES, blank=True, null=True, verbose_name="Kateqoriya")  
    is_active = models.BooleanField(default=True, verbose_name="Aktivdir")
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name="listings", verbose_name="Satıcı")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Yaradılma vaxtı")
    id = models.BigAutoField(primary_key=True)
    seller_name = models.CharField(max_length=64, blank=True, null=True, verbose_name="Satıcının adı")
    phone_number = models.CharField(max_length=20, blank=True, null=True, verbose_name="Əlaqə nömrəsi")
    winner = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="won_listings", verbose_name="Qalib alıcı")
    end_time = models.DateTimeField(null=True, blank=True, verbose_name="Bitmə vaxtı")

    # Beh / Təminat Faizi Seçimi (Yüksək dəyərli mallar / Avtomobil üçün)
    DEPOSIT_CHOICES = [
        (100, '100% - Tam Təminat (Standart mallar)'),
        (50, '50% Beh (Dəyərli elektronika və avadanlıq)'),
        (20, '20% Beh (Bahalı texnika və lüks mallar)'),
        (10, '10% Beh (Avtomobil və yüksək dəyərli əmlak)'),
    ]
    deposit_percentage = models.PositiveIntegerField(
        default=100,
        choices=DEPOSIT_CHOICES,
        verbose_name="Tələb olunan Beh/Depozit faizi (%)"
    )

    # Anti-Sniping (Son 2 dəqiqədə təklif verildikdə vaxtın avtomatik uzadılması)
    anti_sniping_enabled = models.BooleanField(default=True, verbose_name="Anti-Sniping aktivdir")
    anti_sniping_count = models.PositiveIntegerField(default=0, verbose_name="Anti-sniping uzadılma sayı")

    def __str__(self):
        return f"{self.title} ({self.starting_bid} ₼)"

    @property
    def display_image(self):
        if self.image:
            try:
                return self.image.url
            except Exception:
                pass
        if self.image_url:
            return self.image_url
        return None

    @property
    def current_bid(self):
        if hasattr(self, '_prefetched_objects_cache') and 'bids' in self._prefetched_objects_cache:
            cached_bids = self._prefetched_objects_cache['bids']
            return cached_bids[0].amount if cached_bids else self.starting_bid
        highest_bid = self.bids.order_by('-amount').first()
        return highest_bid.amount if highest_bid else self.starting_bid

    @property
    def has_bids(self):
        if hasattr(self, '_prefetched_objects_cache') and 'bids' in self._prefetched_objects_cache:
            return len(self._prefetched_objects_cache['bids']) > 0
        return self.bids.exists()

    @property
    def next_minimum_bid(self):
        if hasattr(self, '_prefetched_objects_cache') and 'bids' in self._prefetched_objects_cache:
            cached_bids = self._prefetched_objects_cache['bids']
            if cached_bids:
                return cached_bids[0].amount + self.min_increment
            return self.starting_bid
        highest = self.bids.order_by('-amount').first()
        if highest:
            return highest.amount + self.min_increment
        return self.starting_bid

    @property
    def has_expired(self):
        if self.end_time and timezone.now() >= self.end_time:
            return True
        return False

    @property
    def is_paid(self):
        try:
            return self.auction_result.payment_status == 'PAID'
        except Exception:
            return False

    @property
    def payment_status(self):
        try:
            return self.auction_result.payment_status
        except Exception:
            return None

    def get_required_deposit(self, bid_amount):
        """Bu məhsula təklif vermək üçün cüzdanda tələb olunan beh/təminat məbləği (AZN)."""
        pct = Decimal(self.deposit_percentage) / Decimal('100.00')
        return (bid_amount * pct).quantize(Decimal('0.01'))

    def trigger_anti_sniping(self):
        """
        Son 2 dəqiqədə təklif verildikdə hərrac vaxtını avtomatik 2 dəqiqə uzadır (Anti-Sniping).
        """
        if not self.anti_sniping_enabled or not self.end_time or not self.is_active:
            return False

        now = timezone.now()
        seconds_left = (self.end_time - now).total_seconds()
        # Əgər bitməyə 120 saniyə (2 dəqiqə) və ya daha az qalıbsa
        if 0 < seconds_left <= 120:
            self.end_time = self.end_time + timezone.timedelta(minutes=2)
            self.anti_sniping_count += 1
            self.save(update_fields=['end_time', 'anti_sniping_count'])
            return True
        return False

    def check_and_update_status(self):
        """Hərrac vaxtı bitdikdə avtomatik bağlayır, qalibi təyin edir və bildiriş göndərir (BR-7, BR-9)."""
        if self.is_active and self.end_time and timezone.now() >= self.end_time:
            self.is_active = False
            highest_bid = self.bids.order_by('-amount').first()
            if highest_bid:
                self.winner = highest_bid.bidder
                # Yekun nəticəni AuctionResult-da saxlayırıq (1:1 əlaqə)
                AuctionResult.objects.get_or_create(
                    listing=self,
                    defaults={'winning_bid': highest_bid}
                )
                # Qalibə bildiriş göndərilir (WON)
                try:
                    Notification.objects.create(
                        recipient=self.winner,
                        sender=self.creator,
                        notification_type='won',
                        title=f"Təbriklər! '{self.title}' hərracını qazandınız!",
                        message=f"'{self.title}' məhsulu üçün verdiyiniz {highest_bid.amount} ₼ məbləğində təklif qalib oldu.",
                        listing=self
                    )
                    # Digər iştirakçılara bildiriş (LOST)
                    other_bidders = set(self.bids.exclude(bidder=self.winner).values_list('bidder', flat=True))
                    for bidder_id in other_bidders:
                        Notification.objects.create(
                            recipient_id=bidder_id,
                            sender=self.creator,
                            notification_type='lost',
                            title=f"Hərrac yekunlaşdı: '{self.title}'",
                            message=f"'{self.title}' hərracı başa çatdı və digər alıcı qalib oldu.",
                            listing=self
                        )
                except Exception:
                    pass
            self.save()
            return True
        return False


class ProductImage(models.Model):
    """Məhsula aid əlavə şəkillər (PRODUCT_IMAGE entity)."""
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name="gallery_images")
    image = models.ImageField(upload_to='images/', blank=True, null=True)
    image_url = models.URLField(blank=True, null=True)
    sort_order = models.IntegerField(default=1)

    class Meta:
        ordering = ['sort_order']

    def __str__(self):
        return f"Şəkil ({self.sort_order}) - {self.listing.title}"


class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name="comments")
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}: {self.content[:20]}"


class Watchlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="watchlist_items")
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE)
    is_unread = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.username} -> {self.listing.title} ({'unread' if self.is_unread else 'read'})"


class Bid(models.Model):
    bidder = models.ForeignKey(User, on_delete=models.CASCADE, related_name="bids")
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name="bids")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.bidder.username} - {self.amount} ₼ on {self.listing.title}"


class AutoBid(models.Model):
    """Maksimum Təklif Limiti və Avtomatlaşdırılmış Rəqabət (Proxy / Auto Bidding)."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="auto_bids", verbose_name="İstifadəçi")
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name="auto_bids", verbose_name="Hərrac elanı")
    max_amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Maksimum Təklif Limiti (AZN)")
    is_active = models.BooleanField(default=True, verbose_name="Aktivdir")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Yaradılma vaxtı")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Yenilənmə vaxtı")

    class Meta:
        unique_together = ('user', 'listing')
        verbose_name = "Avtomatik Təklif"
        verbose_name_plural = "Avtomatik Təkliflər"

    def __str__(self):
        return f"AutoBid: {self.user.username} -> {self.listing.title} (Max: {self.max_amount} ₼)"


class AuctionResult(models.Model):
    """Qalibiyyət / Yekun Nəticə və Sifariş Ödənişi (AUCTION_RESULT entity - 1:1 əlaqə)."""
    PAYMENT_STATUS_CHOICES = [
        ('PENDING', 'Ödəniş Gözlənilir'),
        ('PAID', 'Ödənildi'),
        ('CANCELLED', 'İmtina Edildi / Ödənilmədi'),
    ]

    listing = models.OneToOneField(Listing, on_delete=models.CASCADE, related_name="auction_result")
    winning_bid = models.OneToOneField(Bid, on_delete=models.CASCADE, related_name="result")
    closed_at = models.DateTimeField(auto_now_add=True)
    
    # Sifariş və Ödəniş İzləmə
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='PENDING', verbose_name="Ödəniş statusu")
    paid_at = models.DateTimeField(null=True, blank=True, verbose_name="Ödəniş vaxtı")
    delivery_city = models.CharField(max_length=64, blank=True, null=True, verbose_name="Çatdırılma şəhəri")
    delivery_address = models.TextField(blank=True, null=True, verbose_name="Çatdırılma ünvanı")
    delivery_phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Əlaqə nömrəsi")
    delivery_notes = models.TextField(blank=True, null=True, verbose_name="Kuryer qeydi")

    def __str__(self):
        return f"Nəticə: {self.listing.title} - Qalib: {self.winning_bid.bidder.username} ({self.winning_bid.amount} ₼) - {self.get_payment_status_display()}"


class WalletTransaction(models.Model):
    """Cüzdan və Maliyyə Əməliyyatları Tarixçəsi."""
    TRANSACTION_TYPES = [
        ('DEPOSIT', 'Balans Artırılması'),
        ('WITHDRAW', 'Balansdan Çıxarış'),
        ('AUCTION_PAYMENT', 'Hərrac Ödənişi'),
        ('AUCTION_EARNINGS', 'Satış Gəliri'),
        ('PENALTY', 'Cərimə / Etibarsızlıq Tutulması'),
        ('REFUND', 'Geri Qaytarılma'),
    ]
    STATUS_CHOICES = [
        ('SUCCESS', 'Uğurlu'),
        ('PENDING', 'Gözlənilir'),
        ('FAILED', 'Uğursuz'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wallet_transactions', verbose_name="İstifadəçi")
    transaction_type = models.CharField(max_length=32, choices=TRANSACTION_TYPES, verbose_name="Əməliyyat növü")
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Məbləğ (₼)")
    balance_after = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), verbose_name="Əməliyyatdan sonrakı balans")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='SUCCESS', verbose_name="Status")
    description = models.CharField(max_length=255, blank=True, null=True, verbose_name="Təsvir")
    listing = models.ForeignKey(Listing, on_delete=models.SET_NULL, null=True, blank=True, related_name='transactions', verbose_name="Əlaqəli elan")
    card_last_four = models.CharField(max_length=4, blank=True, null=True, verbose_name="Kartın son 4 rəqəmi")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Tarix")

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.get_transaction_type_display()}: {self.amount} ₼ ({self.created_at.strftime('%d.%m.%Y %H:%M')})"


class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('won', 'Qalibiyyət Bildirişi (WON)'),
        ('lost', 'Məğlubiyyət Bildirişi (LOST)'),
        ('bid', 'Yeni Təklif'),
        ('outbid', 'Təklif Keçildi'),
        ('payment', 'Ödəniş / Cüzdan Bildirişi'),
        ('delivery', 'Çatdırılma / Sifariş Bildirişi'),
        ('comment', 'Şərh'),
        ('follow', 'İzləmə'),
        ('closed', 'Hərrac Bağlandı'),
        ('report', 'Xəta / Şikayət Bildirişi'),
    ]

    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    sender = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="sent_notifications")
    notification_type = models.CharField(max_length=32, choices=NOTIFICATION_TYPES, default='comment')
    title = models.CharField(max_length=128)
    message = models.TextField()
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, null=True, blank=True, related_name="notifications")
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Bildiriş ({self.recipient.username}): {self.title}"


class Follow(models.Model):
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name="following_relations")
    following = models.ForeignKey(User, on_delete=models.CASCADE, related_name="follower_relations")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('follower', 'following')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.follower.username} -> {self.following.username}"


class Report(models.Model):
    REPORT_TYPES = [
        ('bug', 'Texniki Xəta / Sayt Nasazlığı'),
        ('fake_product', 'Saxta Məhsul / Qayda Pozuntusu'),
        ('seller_issue', 'Satıcıdan Şikayət'),
        ('payment_issue', 'Ödəniş / Depozit Problemi'),
        ('other', 'Digər Təklif və ya Şikayət'),
    ]

    STATUS_CHOICES = [
        ('PENDING', 'Gözləmədə (Yeni)'),
        ('IN_REVIEW', 'Baxılır'),
        ('RESOLVED', 'Həll Edildi'),
        ('REJECTED', 'İmtina Edildi'),
    ]

    reporter = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="submitted_reports", verbose_name="Bildirən İstifadəçi")
    reporter_email = models.EmailField(blank=True, null=True, verbose_name="Əlaqə E-poçtu")
    listing = models.ForeignKey(Listing, on_delete=models.SET_NULL, null=True, blank=True, related_name="reports", verbose_name="Əlaqəli Məhsul")
    report_type = models.CharField(max_length=32, choices=REPORT_TYPES, default='bug', verbose_name="Xətanın Növü")
    title = models.CharField(max_length=150, verbose_name="Başlıq")
    description = models.TextField(verbose_name="Ətraflı İzah")
    screenshot = models.ImageField(upload_to='reports/', blank=True, null=True, verbose_name="Ekran Görüntüsü")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING', verbose_name="Status")
    admin_notes = models.TextField(blank=True, null=True, verbose_name="Admin Qeydi")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Bildirilmə Tarixi")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Yenilənmə Tarixi")

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Xəta Bildirişi"
        verbose_name_plural = "Xəta Bildirişləri və Şikayətlər"

    def __str__(self):
        return f"[{self.get_status_display()}] {self.title} ({self.get_report_type_display()})"
