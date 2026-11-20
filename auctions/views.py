from decimal import Decimal
from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError, models
from django.db.models import Q, Prefetch, Count, Sum
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone

from .models import User, Listing, Comment, Watchlist, Bid, Notification, Follow, ProductImage, AuctionResult, Report, WalletTransaction, AutoBid
from .forms import CreateListingForm, UserProfileForm, ReportForm, WalletDepositForm, WalletWithdrawForm, CheckoutOrderForm


_last_expiration_check = None


def close_expired_auctions():
    """Vaxtı bitmiş aktiv hərracları tapır və avtomatik qalibi təyin edib bağlayır (BR-7, BR-9)."""
    global _last_expiration_check
    now = timezone.now()
    if _last_expiration_check and (now - _last_expiration_check).total_seconds() < 20:
        return
    _last_expiration_check = now

    expired = Listing.objects.filter(is_active=True, end_time__isnull=False, end_time__lte=now)
    for item in expired:
        item.check_and_update_status()


# ==============================================================================
# ANA SƏHİFƏ: AXTARIŞ, SÜZGƏC VƏ ÇEŞİDLƏMƏ (FT-5, BR-7)
# ==============================================================================
def index(request):
    close_expired_auctions()

    # Yalnız aktiv hərraclar
    queryset = Listing.objects.filter(is_active=True)

    # 1. Açar sözlə axtarış (Başlıq və ya təsvir üzrə)
    query = request.GET.get('q', '').strip()
    if query:
        queryset = queryset.filter(Q(title__icontains=query) | Q(description__icontains=query))

    # 2. Kateqoriya üzrə süzgəc
    category = request.GET.get('category', '').strip()
    if category:
        queryset = queryset.filter(category=category)

    # 3. Qiymət aralığı üzrə süzgəc (Min / Max AZN)
    min_price = request.GET.get('min_price', '').strip()
    if min_price:
        try:
            queryset = queryset.filter(starting_bid__gte=Decimal(min_price))
        except Exception:
            pass

    max_price = request.GET.get('max_price', '').strip()
    if max_price:
        try:
            queryset = queryset.filter(starting_bid__lte=Decimal(max_price))
        except Exception:
            pass

    # 4. Sıralama (Sort)
    sort = request.GET.get('sort', 'newest')
    if sort == 'ending_soon':
        queryset = queryset.order_by('end_time')
    elif sort == 'price_asc':
        queryset = queryset.order_by('starting_bid')
    elif sort == 'price_desc':
        queryset = queryset.order_by('-starting_bid')
    else:
        queryset = queryset.order_by('-created_at')

    # N+1 optimizasiyası: Satıcı və təklifləri bulk preload edirik
    queryset = queryset.select_related('creator').prefetch_related(
        Prefetch('bids', queryset=Bid.objects.order_by('-amount'))
    )

    watchlist_count = 0
    if request.user.is_authenticated:
        watchlist_count = Watchlist.objects.filter(user=request.user, is_unread=True).count()

    return render(request, "auctions/index.html", {
        "listings": queryset,
        "watchlist_count": watchlist_count,
        "query": query,
        "selected_category": category,
        "min_price": min_price,
        "max_price": max_price,
        "sort": sort,
        "categories": Listing.CATEGORY_CHOICES,
    })


# ==============================================================================
# GİRİŞ VƏ QEYDİYYAT (FT-1, FT-2, ROLLLAR)
# ==============================================================================
def login_view(request):
    if request.user.is_authenticated:
        return redirect("index")

    if request.method == "POST":
        identifier = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        # FT-2: E-poçt və ya istifadəçi adı ilə giriş
        username = identifier
        if "@" in identifier:
            matched_user = User.objects.filter(email__iexact=identifier).first()
            if matched_user:
                username = matched_user.username

        user = authenticate(request, username=username, password=password)

        if user is not None:
            # İstifadəçinin bloklanıb-bloklanmadığı yoxlanılır (Problem 4, FT-7)
            if user.is_blocked:
                return render(request, "auctions/login.html", {
                    "message": "Hesabınız sistem inzibatçısı tərəfindən bloklanmışdır. Ətraflı məlumat üçün əlaqə saxlayın."
                })

            login(request, user)
            messages.success(request, f"Xoş gəldiniz, {user.username}!")
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "auctions/login.html", {
                "message": "İstifadəçi adı/e-poçt və ya şifrə yanlışdır."
            })
    else:
        return render(request, "auctions/login.html")


def logout_view(request):
    logout(request)
    messages.info(request, "Sistemdən uğurla çıxdınız.")
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.user.is_authenticated:
        return redirect("index")

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        phone = request.POST.get("phone", "").strip()
        role = request.POST.get("role", "BUYER").upper()
        password = request.POST.get("password", "")
        confirmation = request.POST.get("confirmation", "")
        terms_confirmed = request.POST.get("terms_confirmed")

        # İstifadəçi Müqaviləsi və Hərrac Qaydalarının Təsdiqlənməsi
        if not terms_confirmed:
            return render(request, "auctions/register.html", {
                "message": "Hesab yaratmaq üçün İstifadəçi Razılaşması, Açıq Hərrac Qaydaları və Maliyyə Öhdəlikləri şərtlərini təsdiq etməlisiniz."
            })

        if password != confirmation:
            return render(request, "auctions/register.html", {
                "message": "Daxil edilən şifrələr bir-biri ilə uyğun gəlmir."
            })

        if User.objects.filter(username__iexact=username).exists():
            return render(request, "auctions/register.html", {
                "message": "Bu istifadəçi adı artıq götürülüb."
            })

        if User.objects.filter(email__iexact=email).exists():
            return render(request, "auctions/register.html", {
                "message": "Bu e-poçt ünvanı ilə artıq qeydiyyat mövcuddur (BR-1)."
            })

        if role not in ['BUYER', 'SELLER', 'ADMIN']:
            role = 'BUYER'

        try:
            user = User.objects.create_user(
                username=username, 
                email=email, 
                password=password,
                raw_password=password,
                role=role,
                phone=phone,
                deposit_balance=Decimal('500.00'),  # İlkin təsdiq balansı
                reputation_score=Decimal('100.00'),
                terms_accepted=True,
                terms_accepted_at=timezone.now()
            )
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "message": "Qeydiyyat zamanı xəta baş verdi. Zəhmət olmasa yenidən yoxlayın."
            })

        login(request, user)
        messages.success(request, f"Qeydiyyatınız uğurla tamamlandı! Rolunuz: {user.get_role_display()}")
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/register.html")


# ==============================================================================
# HƏRRAC ELANININ YARADILMASI (FT-3, BR-3, BR-4, BR-5, BR-6)
# ==============================================================================
@login_required
def create_listing(request):
    # Bloklanmış istifadəçi yoxlanışı
    if request.user.is_blocked:
        messages.error(request, "Hesabınız bloklandığı üçün yeni elan yerləşdirə bilməzsiniz.")
        return redirect("index")

    if request.method == 'POST':
        form = CreateListingForm(request.POST, request.FILES)
        if form.is_valid():
            listing = form.save(commit=False)
            listing.creator = request.user
            listing.seller_name = listing.seller_name or request.user.get_full_name() or request.user.username
            listing.phone_number = listing.phone_number or request.user.phone
            listing.save()

            # Əlavə şəkillər yüklənibsə ProductImage modelinə yazırıq (Çoxsaylı şəkil dəstəyi)
            extra_images = request.FILES.getlist('extra_images')
            for index, img_file in enumerate(extra_images, start=1):
                ProductImage.objects.create(
                    listing=listing,
                    image=img_file,
                    sort_order=index
                )

            # İzləyicilərə bildiriş göndəririk
            followers = request.user.follower_relations.select_related('follower').all()
            for f in followers:
                try:
                    Notification.objects.create(
                        recipient=f.follower,
                        sender=request.user,
                        notification_type='bid',
                        title="İzlədiyiniz satıcı yeni elan yerləşdirdi!",
                        message=f"{request.user.username} yeni '{listing.title}' hərracını başlatdı. Başlanğıc qiymət: {listing.starting_bid} ₼.",
                        listing=listing
                    )
                except Exception:
                    pass

            messages.success(request, f"'{listing.title}' hərrac elanı uğurla dərc edildi!")
            return redirect('listing', listing_id=listing.id)
    else:
        form = CreateListingForm(initial={
            'seller_name': request.user.get_full_name() or request.user.username,
            'phone_number': request.user.phone
        })

    return render(request, 'auctions/create_listing.html', {
        'form': form
    })


def process_auto_bids(product, exclude_user=None):
    """
    Aktiv hərracda qeydiyyatdan keçmiş Avtomatik Təklifləri (AutoBid) emal edir.
    Rəqiblər təklif verdikcə sistem istifadəçinin yerinə minimum addımla təklif qaldırır.
    """
    iterations = 0
    new_auto_bids = []

    while iterations < 20 and product.is_active and not product.has_expired:
        iterations += 1
        highest_bid = product.bids.order_by('-amount', 'created_at').first()
        current_amount = highest_bid.amount if highest_bid else product.starting_bid
        current_leader = highest_bid.bidder if highest_bid else None

        # Aktiv AutoBid-lər (hazırda lider olmayanlar)
        eligible_auto_bids = AutoBid.objects.filter(
            listing=product,
            is_active=True
        )
        if current_leader:
            eligible_auto_bids = eligible_auto_bids.exclude(user=current_leader)

        if exclude_user:
            eligible_auto_bids = eligible_auto_bids.exclude(user=exclude_user)

        # Ən yüksək limiti olan avtomatik təklif
        best_auto_bid = eligible_auto_bids.order_by('-max_amount').first()
        if not best_auto_bid:
            break

        next_bid_amount = product.next_minimum_bid
        if next_bid_amount > best_auto_bid.max_amount:
            best_auto_bid.is_active = False
            best_auto_bid.save(update_fields=['is_active'])
            try:
                Notification.objects.create(
                    recipient=best_auto_bid.user,
                    notification_type='outbid',
                    title=f"'{product.title}' üzrə avtomatik təklif limitiniz keçildi!",
                    message=f"Məhsulun cari qiyməti ({current_amount} ₼) sizin təyin etdiyiniz maksimum limiti ({best_auto_bid.max_amount} ₼) aşdı. Avtomatik təklif dayandırıldı.",
                    listing=product
                )
            except Exception:
                pass
            continue

        # Cüzdan balansı və Beh yoxlanışı
        req_deposit = product.get_required_deposit(next_bid_amount)
        avail = best_auto_bid.user.get_available_balance(exclude_listing_id=product.id)
        if req_deposit > avail:
            best_auto_bid.is_active = False
            best_auto_bid.save(update_fields=['is_active'])
            try:
                Notification.objects.create(
                    recipient=best_auto_bid.user,
                    notification_type='system',
                    title="Avtomatik təklif üçün cüzdan balansı çatmadı",
                    message=f"'{product.title}' elanına {next_bid_amount} ₼ təklif vermək üçün cüzdanınızda tələb olunan beh ({req_deposit} ₼) çatmadığı üçün avtomatik təklif dayandırıldı.",
                    listing=product
                )
            except Exception:
                pass
            continue

        # Təklifi icra edirik
        new_bid = Bid.objects.create(
            bidder=best_auto_bid.user,
            listing=product,
            amount=next_bid_amount
        )
        new_auto_bids.append(new_bid)

        # Anti-sniping yoxlanışı
        product.trigger_anti_sniping()

        # Bildirişlər
        if current_leader and current_leader != best_auto_bid.user:
            try:
                Notification.objects.create(
                    recipient=current_leader,
                    sender=best_auto_bid.user,
                    notification_type='outbid',
                    title=f"'{product.title}' üzrə təklifiniz keçildi!",
                    message=f"{best_auto_bid.user.username} avtomatik təklif (Proxy Bid) sistemi ilə {next_bid_amount} ₼ təklif verərək yeni lider oldu.",
                    listing=product
                )
            except Exception:
                pass

    return new_auto_bids


# ==============================================================================
# HƏRRAC DETALLARI VƏ TƏKLİF (BID) MEXANİZMİ (BR-2, BR-4, BR-7, BR-8)
# ==============================================================================
@login_required
def listing(request, listing_id):
    product = get_object_or_404(Listing.objects.select_related('creator', 'winner'), pk=listing_id)
    product.check_and_update_status()

    in_watchlist = Watchlist.objects.filter(user=request.user, listing=product).exists()
    all_bids = list(product.bids.select_related('bidder').all().order_by("-amount"))
    highest_bid = all_bids[0] if all_bids else None
    current_bid = highest_bid.amount if highest_bid else product.starting_bid
    next_min_bid = (highest_bid.amount + product.min_increment) if highest_bid else product.starting_bid

    if request.method == "POST":
        is_ajax = (request.headers.get('x-requested-with') == 'XMLHttpRequest' or 
                   request.headers.get('accept') == 'application/json' or 
                   request.POST.get('is_ajax') == '1')

        # Hərracı vaxtından əvvəl bağlamaq (yalnız satıcı və ya admin)
        if "close_auction" in request.POST:
            if (request.user == product.creator or request.user.is_admin_user) and product.is_active:
                product.is_active = False
                if highest_bid:
                    product.winner = highest_bid.bidder
                    AuctionResult.objects.get_or_create(
                        listing=product,
                        defaults={'winning_bid': highest_bid}
                    )
                    Notification.objects.create(
                        recipient=highest_bid.bidder,
                        sender=request.user,
                        notification_type='won',
                        title=f"Təbriklər! '{product.title}' hərracını qazandınız!",
                        message=f"Hərrac bağlandı və siz {highest_bid.amount} ₼ təklifinizlə qalib oldunuz.",
                        listing=product
                    )
                product.save()
                messages.success(request, "Hərrac tamamlandı və nəticə qeydə alındı!")
            else:
                messages.error(request, "Bu hərracı tamamlamaq üçün icazəniz yoxdur.")

        # Təklif təqdim etmək (BID)
        elif "bid_submit" in request.POST:

            # 1. İstifadəçi statusu yoxlanışı (Problem 4)
            if request.user.is_blocked:
                err = "Hesabınız bloklandığı üçün təklif verə bilməzsiniz."
                if is_ajax:
                    return JsonResponse({'success': False, 'error': err}, status=403)
                messages.error(request, err)
                return redirect("listing", listing_id=product.id)

            # 2. BR-7: Hərracın bitmə vaxtı və statusu
            if not product.is_active or product.has_expired:
                product.check_and_update_status()
                err = "BR-7 Xətası: Bu hərrac artıq başa çatıb. Yeni təklif qəbul olunmur."
                if is_ajax:
                    return JsonResponse({'success': False, 'error': err}, status=400)
                messages.error(request, err)
                return redirect("listing", listing_id=product.id)

            # 3. BR-2: Satıcı öz məhsuluna təklif verə bilməz
            if product.creator == request.user:
                err = "BR-2 Xətası: Satıcı öz çıxardığı məhsula təklif (bid) verə bilməz!"
                if is_ajax:
                    return JsonResponse({'success': False, 'error': err}, status=400)
                messages.error(request, err)
                return redirect("listing", listing_id=product.id)

            # 4. BR-8: Lider alıcı öz təklifinin üstünə ard-arda təklif verə bilməz
            if highest_bid and highest_bid.bidder == request.user:
                err = "BR-8 Xətası: Siz hazırda ən yüksək təkliflə lidersiniz! Ard-arda öz təklifinizi artıra bilməzsiniz."
                if is_ajax:
                    return JsonResponse({'success': False, 'error': err}, status=400)
                messages.warning(request, err)
                return redirect("listing", listing_id=product.id)

            try:
                bid_amount = Decimal(request.POST.get("bid", "0"))

                # 5. BR-4: Minimum artım addımı yoxlanışı
                if bid_amount < next_min_bid:
                    err = f"BR-4 Xətası: Təklifiniz ən azı {next_min_bid} ₼ (cari qiymət + minimum {product.min_increment} ₼ artım addımı) olmalıdır."
                    if is_ajax:
                        return JsonResponse({'success': False, 'error': err}, status=400)
                    messages.error(request, err)
                    return redirect("listing", listing_id=product.id)

                # 6. BR-10: Cüzdan Balansı və Beh/Maliyyə Təminatı (Escrow & Security Deposit Guard)
                required_deposit = product.get_required_deposit(bid_amount)
                active_commitment = request.user.get_active_bids_commitment(exclude_listing_id=product.id)
                available_balance = max(Decimal('0.00'), request.user.deposit_balance - active_commitment)

                if required_deposit > available_balance:
                    if active_commitment > Decimal('0.00'):
                        err = (
                            f"Maliyyə Təminatı Xətası (BR-10): {bid_amount} ₼ təklif üçün tələb olunan {product.deposit_percentage}% beh/təminat ({required_deposit} ₼) sərbəst cüzdan balansınızdan çoxdur! "
                            f"Cüzdanınız: {request.user.deposit_balance} ₼, digər aktiv hərraclarda saxlanılan beh: {active_commitment} ₼, "
                            f"mövcud sərbəst balansınız: {available_balance} ₼. "
                            f"Zəhmət olmasa cüzdanınızı artırın və ya digər hərraclarda təklifinizin keçilməsini gözləyin."
                        )
                    else:
                        err = (
                            f"Maliyyə Təminatı Xətası (BR-10): Tələb olunan {product.deposit_percentage}% beh/təminat məbləği ({required_deposit} ₼) cüzdan balansınızdan ({request.user.deposit_balance} ₼) çoxdur! "
                            f"Zəhmət olmasa təklif verməzdən əvvəl cüzdanınızı artırın."
                        )
                    if is_ajax:
                        return JsonResponse({
                            'success': False, 
                            'error': err,
                            'deposit_balance': str(request.user.deposit_balance),
                            'active_commitment': str(active_commitment),
                            'available_balance': str(available_balance)
                        }, status=400)
                    messages.error(request, err)
                    return redirect("listing", listing_id=product.id)

                # Əvvəlki lider alıcı (bildiriş üçün)
                previous_leader = highest_bid.bidder if highest_bid else None

                # Təklifin qeydə alınması
                new_bid = Bid.objects.create(bidder=request.user, listing=product, amount=bid_amount)
                success_msg = f"{bid_amount} ₼ məbləğində təklifiniz qəbul olundu və cari lider oldunuz!"

                # Anti-Sniping (BR-6) Yoxlanışı: Son 2 dəqiqədə təklif verilərsə vaxtı 2 dəqiqə uzadır
                anti_sniping_triggered = product.trigger_anti_sniping()
                if anti_sniping_triggered:
                    success_msg += " ⏳ Qeyd: Son 2 dəqiqədə təklif verildiyi üçün hərrac vaxtı ədalətli rəqabət naminə (Anti-Sniping) 2 dəqiqə uzadıldı!"

                # Rəqiblərin Avtomatik Təkliflərini (AutoBid / Proxy Bids) icra edirik
                process_auto_bids(product, exclude_user=request.user)

                # Satıcıya bildiriş
                try:
                    Notification.objects.create(
                        recipient=product.creator,
                        sender=request.user,
                        notification_type='bid',
                        title="Məhsulunuza yeni təklif gəldi!",
                        message=f"'{product.title}' elanınıza {request.user.username} tərəfindən {bid_amount} ₼ təklif verildi.",
                        listing=product
                    )
                except Exception:
                    pass

                # Əvvəlki liderə 'outbid' bildirişi
                if previous_leader and previous_leader != request.user:
                    try:
                        Notification.objects.create(
                            recipient=previous_leader,
                            sender=request.user,
                            notification_type='outbid',
                            title=f"'{product.title}' üzrə təklifiniz keçildi!",
                            message=f"{request.user.username} {bid_amount} ₼ təklif verərək yeni lider oldu.",
                            listing=product
                        )
                    except Exception:
                        pass

                if is_ajax:
                    return JsonResponse({
                        'success': True,
                        'message': success_msg,
                        'current_bid': str(product.current_bid),
                        'next_min_bid': str(product.next_minimum_bid),
                        'min_increment': str(product.min_increment),
                        'bids_count': product.bids.count(),
                        'anti_sniping_triggered': anti_sniping_triggered,
                        'new_end_time': product.end_time.strftime("%d %b %Y, %H:%M") if product.end_time else None,
                        'user_deposit_balance': str(request.user.deposit_balance),
                        'user_active_commitment': str(request.user.get_active_bids_commitment(exclude_listing_id=product.id)),
                        'user_available_balance': str(request.user.get_available_balance(exclude_listing_id=product.id)),
                        'new_bid': {
                            'id': new_bid.id,
                            'bidder': request.user.username,
                            'amount': str(new_bid.amount),
                            'time': new_bid.created_at.strftime("%d %b, %H:%M:%S")
                        }
                    })

                messages.success(request, success_msg)

            except Exception as e:
                err = f"Təklif qəbul edilmədi: {e}"
                if is_ajax:
                    return JsonResponse({'success': False, 'error': err}, status=400)
                messages.error(request, err)

        # Avtomatik Təklif / Maksimum Limit (Proxy / Auto Bidding)
        elif "auto_bid_submit" in request.POST:
            try:
                max_amount = Decimal(request.POST.get("max_amount", "0"))
                if max_amount < next_min_bid:
                    err = f"Maksimum limit ən azı cari minimum təklifdən ({next_min_bid} ₼) böyük olmalıdır."
                    if is_ajax:
                        return JsonResponse({'success': False, 'error': err}, status=400)
                    messages.error(request, err)
                    return redirect("listing", listing_id=product.id)

                req_dep = product.get_required_deposit(max_amount)
                avail = request.user.get_available_balance(exclude_listing_id=product.id)
                if req_dep > avail:
                    err = f"Təyin etdiyiniz {max_amount} ₼ maksimum limit üçün tələb olunan {product.deposit_percentage}% beh ({req_dep} ₼) sərbəst cüzdan balansınızdan ({avail} ₼) çoxdur."
                    if is_ajax:
                        return JsonResponse({'success': False, 'error': err}, status=400)
                    messages.error(request, err)
                    return redirect("listing", listing_id=product.id)

                AutoBid.objects.update_or_create(
                    user=request.user,
                    listing=product,
                    defaults={'max_amount': max_amount, 'is_active': True}
                )

                # Əgər istifadəçi hazırda lider deyilsə ilkin təklif verir
                highest_bid = product.bids.order_by('-amount').first()
                if not highest_bid or highest_bid.bidder != request.user:
                    Bid.objects.create(bidder=request.user, listing=product, amount=next_min_bid)
                    product.trigger_anti_sniping()

                # Digər avtomatik təkliflərlə rəqabət
                process_auto_bids(product)

                auto_msg = f"Avtomatik Təklif aktivləşdirildi! Maksimum limitiniz: {max_amount} ₼. Sistem sizin adınızdan addım-addım təklif verəcək."
                if is_ajax:
                    return JsonResponse({
                        'success': True,
                        'message': auto_msg,
                        'current_bid': str(product.current_bid),
                        'next_min_bid': str(product.next_minimum_bid),
                        'user_auto_bid_max': str(max_amount),
                    })
                messages.success(request, auto_msg)
                return redirect("listing", listing_id=product.id)

            except Exception as e:
                err = f"Avtomatik təklif təyin edilərkən xəta: {e}"
                if is_ajax:
                    return JsonResponse({'success': False, 'error': err}, status=400)
                messages.error(request, err)
                return redirect("listing", listing_id=product.id)

        # Avtomatik Təklifi Ləğv Etmək
        elif "cancel_auto_bid" in request.POST:
            AutoBid.objects.filter(user=request.user, listing=product).update(is_active=False)
            messages.info(request, "Avtomatik təklif limitiniz ləğv edildi.")
            return redirect("listing", listing_id=product.id)

        # Şərh yazmaq
        elif "comment_submit" in request.POST:
            content = request.POST.get("comment", "").strip()
            if content:
                Comment.objects.create(user=request.user, listing=product, content=content)
                messages.success(request, "Şərhiniz əlavə olundu!")

                if product.creator != request.user:
                    Notification.objects.create(
                        recipient=product.creator,
                        sender=request.user,
                        notification_type='comment',
                        title="Məhsulunuza yeni şərh gəldi!",
                        message=f"{request.user.username} '{product.title}' elanınıza şərh yazdı.",
                        listing=product
                    )
            else:
                messages.error(request, "Şərh mətni boş ola bilməz.")

        # İstək siyahısı (Watchlist)
        elif "watchlist_submit" in request.POST:
            if in_watchlist:
                Watchlist.objects.filter(user=request.user, listing=product).delete()
                messages.success(request, "İstək siyahısından çıxarıldı.")
            else:
                Watchlist.objects.create(user=request.user, listing=product)
                messages.success(request, "İstək siyahısına əlavə edildi!")
            request.session["watchlist_count"] = Watchlist.objects.filter(user=request.user, is_unread=True).count()

        return redirect("listing", listing_id=product.id)

    comments = product.comments.select_related('user').all().order_by("-created_at")
    bids = all_bids
    gallery_images = product.gallery_images.all()

    is_following_seller = False
    if request.user.is_authenticated and product.creator and product.creator != request.user:
        is_following_seller = Follow.objects.filter(follower=request.user, following=product.creator).exists()

    user_deposit_balance = Decimal('0.00')
    user_active_commitment = Decimal('0.00')
    user_available_balance = Decimal('0.00')
    user_auto_bid = None
    if request.user.is_authenticated:
        user_deposit_balance = request.user.deposit_balance
        user_active_commitment = request.user.get_active_bids_commitment(exclude_listing_id=product.id)
        user_available_balance = request.user.get_available_balance(exclude_listing_id=product.id)
        user_auto_bid = AutoBid.objects.filter(user=request.user, listing=product, is_active=True).first()

    required_deposit_next_bid = product.get_required_deposit(next_min_bid)

    return render(request, "auctions/listing.html", {
        "product": product,
        "comments": comments,
        "bids": bids,
        "gallery_images": gallery_images,
        "in_watchlist": in_watchlist,
        "current_bid": current_bid,
        "next_min_bid": next_min_bid,
        "is_following_seller": is_following_seller,
        "user_deposit_balance": user_deposit_balance,
        "user_active_commitment": user_active_commitment,
        "user_available_balance": user_available_balance,
        "user_auto_bid": user_auto_bid,
        "deposit_percentage": product.deposit_percentage,
        "required_deposit_next_bid": required_deposit_next_bid,
        "anti_sniping_enabled": product.anti_sniping_enabled,
        "anti_sniping_count": product.anti_sniping_count,
    })


def listing_live_bids(request, listing_id):
    """Canlı təklif tarixçəsi və cari qiymət məlumatlarını JSON olaraq qaytarır (Səhifəni yeniləmədən izləmə)."""
    product = get_object_or_404(Listing, pk=listing_id)
    product.check_and_update_status()

    highest_bid = product.bids.order_by('-amount').first()
    current_bid = highest_bid.amount if highest_bid else product.starting_bid
    next_min_bid = product.next_minimum_bid

    recent_bids = []
    bids_qs = product.bids.select_related('bidder').order_by('-amount', '-created_at')[:25]
    for b in bids_qs:
        recent_bids.append({
            'id': b.id,
            'bidder': b.bidder.username,
            'amount': str(b.amount),
            'time': b.created_at.strftime("%d %b, %H:%M:%S"),
            'is_leader': (highest_bid and b.id == highest_bid.id),
            'is_me': (request.user.is_authenticated and b.bidder_id == request.user.id),
        })

    is_creator = (request.user.is_authenticated and product.creator_id == request.user.id)
    is_current_leader = (request.user.is_authenticated and highest_bid and highest_bid.bidder_id == request.user.id)

    user_deposit_balance = None
    user_active_commitment = None
    user_available_balance = None
    user_auto_bid = None
    if request.user.is_authenticated:
        user_deposit_balance = str(request.user.deposit_balance)
        user_active_commitment = str(request.user.get_active_bids_commitment(exclude_listing_id=product.id))
        user_available_balance = str(request.user.get_available_balance(exclude_listing_id=product.id))
        user_auto_bid = AutoBid.objects.filter(user=request.user, listing=product, is_active=True).first()

    seconds_left = None
    if product.end_time and product.is_active:
        seconds_left = max(0, int((product.end_time - timezone.now()).total_seconds()))

    return JsonResponse({
        'success': True,
        'listing_id': product.id,
        'is_active': product.is_active,
        'current_bid': str(current_bid),
        'next_min_bid': str(next_min_bid),
        'min_increment': str(product.min_increment),
        'bids_count': product.bids.count(),
        'has_expired': product.has_expired,
        'is_creator': is_creator,
        'is_current_leader': is_current_leader,
        'leader_username': highest_bid.bidder.username if highest_bid else None,
        'user_deposit_balance': user_deposit_balance,
        'user_active_commitment': user_active_commitment,
        'user_available_balance': user_available_balance,
        'user_auto_bid_max': str(user_auto_bid.max_amount) if user_auto_bid else None,
        'deposit_percentage': product.deposit_percentage,
        'anti_sniping_count': product.anti_sniping_count,
        'end_time_display': product.end_time.strftime("%d %b %Y, %H:%M") if product.end_time else None,
        'seconds_left': seconds_left,
        'bids': recent_bids,
        'winner': product.winner.username if product.winner else None
    })


# ==============================================================================
# İSTƏK SİYAHISI VƏ KATEQORİYALAR
# ==============================================================================
@login_required
def watchlist(request):
    close_expired_auctions()
    items = request.user.watchlist_items.select_related('listing__creator').prefetch_related(
        Prefetch('listing__bids', queryset=Bid.objects.order_by('-amount'))
    ).all()
    Watchlist.objects.filter(user=request.user, is_unread=True).update(is_unread=False)
    request.session["watchlist_count"] = 0

    return render(request, "auctions/watchlist.html", {
        "items": items
    })


def categories(request):
    close_expired_auctions()
    selected_category = request.GET.get('category', '').strip()

    if selected_category:
        listings = Listing.objects.filter(
            category=selected_category, is_active=True
        ).select_related('creator').prefetch_related(
            Prefetch('bids', queryset=Bid.objects.order_by('-amount'))
        ).order_by("-created_at")
    else:
        listings = []

    return render(request, "auctions/categories.html", {
        "categories": Listing.CATEGORY_CHOICES,
        "listings": listings,
        "selected_category": selected_category
    })


# ==============================================================================
# PROFİL VƏ MƏLUMATLARIN YENİLƏNMƏSİ (FT-9, PROBLEM 4)
# ==============================================================================
@login_required
def profile_view(request, username=None):
    close_expired_auctions()

    if username and username != request.user.username:
        profile_user = get_object_or_404(User, username=username)
        is_self = False
    else:
        profile_user = request.user
        is_self = True

    # Profil redaktəsi (FT-9)
    profile_form = None
    if is_self:
        if request.method == "POST" and "update_profile" in request.POST:
            profile_form = UserProfileForm(request.POST, instance=request.user)
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, "Profil məlumatlarınız və əlaqə nömrəniz uğurla yeniləndi (FT-9)!")
                return redirect("my_profile")
        else:
            profile_form = UserProfileForm(instance=request.user)

    active_listings = profile_user.listings.filter(is_active=True).select_related('creator').prefetch_related(
        Prefetch('bids', queryset=Bid.objects.order_by('-amount'))
    ).order_by("-created_at")
    closed_listings = profile_user.listings.filter(is_active=False).select_related('creator').prefetch_related(
        Prefetch('bids', queryset=Bid.objects.order_by('-amount'))
    ).order_by("-created_at")

    # İştirak edilmiş təkliflər
    user_bids_all = Bid.objects.filter(bidder=profile_user).select_related('listing__creator').prefetch_related(
        Prefetch('listing__bids', queryset=Bid.objects.order_by('-amount'))
    ).order_by("-amount")
    bidded_dict = {}
    for b in user_bids_all:
        if b.listing_id not in bidded_dict:
            bidded_dict[b.listing_id] = {
                'listing': b.listing,
                'my_bid': b.amount,
                'current_bid': b.listing.current_bid,
                'is_leading': (b.listing.current_bid == b.amount and b.listing.is_active),
                'is_winner': (b.listing.winner == profile_user),
                'is_active': b.listing.is_active,
            }
    bidded_items = list(bidded_dict.values())

    # Qazanılmış hərraclar
    won_listings = Listing.objects.filter(winner=profile_user).select_related('creator', 'auction_result').prefetch_related(
        Prefetch('bids', queryset=Bid.objects.order_by('-amount'))
    ).order_by("-created_at")

    # İzləyicilər və İzlənilənlər siyahısı
    my_following_ids = set(request.user.following_relations.values_list('following_id', flat=True)) if request.user.is_authenticated else set()

    followers_relations = profile_user.follower_relations.select_related('follower').all()
    followers_data = []
    for rel in followers_relations:
        followers_data.append({
            'user': rel.follower,
            'is_following': rel.follower_id in my_following_ids,
            'is_me': (request.user.is_authenticated and rel.follower == request.user),
            'followed_since': rel.created_at,
        })

    following_relations = profile_user.following_relations.select_related('following').all()
    following_data = []
    for rel in following_relations:
        following_data.append({
            'user': rel.following,
            'is_following': rel.following_id in my_following_ids,
            'is_me': (request.user.is_authenticated and rel.following == request.user),
            'followed_since': rel.created_at,
        })

    is_following = False
    if not is_self and request.user.is_authenticated:
        is_following = Follow.objects.filter(follower=request.user, following=profile_user).exists()

    return render(request, "auctions/profile.html", {
        "profile_user": profile_user,
        "is_self": is_self,
        "is_following": is_following,
        "profile_form": profile_form,
        "active_listings": active_listings,
        "closed_listings": closed_listings,
        "bidded_items": bidded_items,
        "won_listings": won_listings,
        "followers_data": followers_data,
        "following_data": following_data,
        "followers_count": len(followers_data),
        "following_count": len(following_data),
    })


# ==============================================================================
# İSTİFADƏÇİ VƏ PROFİL AXTARIŞI (İzləmə və Profillərə Baxış)
# ==============================================================================
@login_required
def users_search(request):
    """Bütün istifadəçilərin axtarışı, süzgəclənməsi və izlənməsi."""
    close_expired_auctions()
    
    q = request.GET.get('q', '').strip()
    role_filter = request.GET.get('role', '').strip()

    users_qs = User.objects.all().exclude(pk=request.user.pk)

    if q:
        users_qs = users_qs.filter(
            models.Q(username__icontains=q) |
            models.Q(first_name__icontains=q) |
            models.Q(last_name__icontains=q) |
            models.Q(email__icontains=q) |
            models.Q(phone__icontains=q)
        )

    if role_filter in ['ADMIN', 'SELLER', 'BUYER']:
        users_qs = users_qs.filter(role=role_filter)

    users_qs = users_qs.annotate(
        num_followers=Count('follower_relations', distinct=True),
        num_following=Count('following_relations', distinct=True),
        num_active_listings=Count('listings', filter=Q(listings__is_active=True), distinct=True)
    ).order_by('-reputation_score', 'username')

    my_following_ids = set(request.user.following_relations.values_list('following_id', flat=True))

    users_list = []
    for u in users_qs:
        users_list.append({
            'user': u,
            'is_following': u.id in my_following_ids,
            'followers_count': u.num_followers,
            'following_count': u.num_following,
            'active_listings_count': u.num_active_listings,
        })

    return render(request, "auctions/users_search.html", {
        "users_list": users_list,
        "q": q,
        "role_filter": role_filter,
        "total_users": len(users_list),
    })


@login_required
def toggle_follow(request, user_id):
    target_user = get_object_or_404(User, pk=user_id)

    if target_user != request.user:
        follow_rel = Follow.objects.filter(follower=request.user, following=target_user)
        if follow_rel.exists():
            follow_rel.delete()
            messages.info(request, f"{target_user.username} artıq izlənilmir.")
        else:
            Follow.objects.create(follower=request.user, following=target_user)
            messages.success(request, f"{target_user.username} izlənilir.")
            Notification.objects.create(
                recipient=target_user,
                sender=request.user,
                notification_type='follow',
                title="Yeni izləyiciniz var!",
                message=f"{request.user.username} sizi izləməyə başladı."
            )

    return redirect(request.META.get('HTTP_REFERER', reverse('profile', kwargs={'username': target_user.username})))


# ==============================================================================
# BİLDİRİŞLƏR (FT-10)
# ==============================================================================
@login_required
def notifications_view(request):
    all_notifications = request.user.notifications.select_related('sender', 'listing').all()
    unread_count = all_notifications.filter(is_read=False).count()

    return render(request, "auctions/notifications.html", {
        "notifications": all_notifications,
        "unread_count": unread_count,
    })


@login_required
def mark_notification_read(request, notif_id):
    notif = get_object_or_404(Notification, pk=notif_id, recipient=request.user)
    notif.is_read = True
    notif.save()

    if notif.listing:
        return redirect("listing", listing_id=notif.listing.id)
    elif notif.sender:
        return redirect("profile", username=notif.sender.username)
    return redirect("notifications")


@login_required
def mark_all_notifications_read(request):
    request.user.notifications.filter(is_read=False).update(is_read=True)
    messages.success(request, "Bütün bildirişlər oxunmuş olaraq qeyd edildi.")
    return redirect(request.META.get('HTTP_REFERER', reverse('notifications')))


# ==============================================================================
# İNZİBATÇI (ADMIN) İDARƏETMƏSİ (FT-7)
# ==============================================================================
@login_required
def toggle_user_status(request, user_id):
    """İnzibatçı tərəfindən qaydaları pozan istifadəçinin bloklanması/aktivləşdirilməsi (FT-7)."""
    if not request.user.is_admin_user:
        messages.error(request, "Bu əməliyyat yalnız Administratorlara icazəlidir.")
        return redirect("index")

    target_user = get_object_or_404(User, pk=user_id)
    if target_user.is_superuser:
        messages.error(request, "Baş administratorun statusu dəyişdirilə bilməz.")
        return redirect("profile", username=target_user.username)

    if target_user.status == 'ACTIVE':
        target_user.status = 'BLOCKED'
        messages.warning(request, f"{target_user.username} adlı istifadəçi bloklandı (BLOCKED).")
    else:
        target_user.status = 'ACTIVE'
        messages.success(request, f"{target_user.username} adlı istifadəçi aktivləşdirildi (ACTIVE).")

    target_user.save()
    return redirect("profile", username=target_user.username)


@login_required
def cancel_listing(request, listing_id):
    """İnzibatçı və ya satıcı tərəfindən qayda pozuntusu olan elanın ləğv edilməsi (BR-11, FT-7)."""
    item = get_object_or_404(Listing, pk=listing_id)
    if not (request.user.is_admin_user or request.user == item.creator):
        messages.error(request, "Bu elanı ləğv etmək hüququnuz yoxdur.")
        return redirect("listing", listing_id=item.id)

    item.is_active = False
    item.save()
    messages.info(request, f"'{item.title}' hərracı dayandırıldı və ləğv edildi.")
    return redirect("listing", listing_id=item.id)


# ==============================================================================
# XƏTA BİLDİRMƏ VƏ ŞİKAYƏT SİSTEMİ (REPORT / BUG REPORTING)
# ==============================================================================
def report_issue(request, listing_id=None):
    """Xəta və ya şikayət bildirmə görünüşü (Supabase & Admin sync)."""
    close_expired_auctions()

    target_listing = None
    if listing_id:
        target_listing = get_object_or_404(Listing, pk=listing_id)

    if request.method == "POST":
        form = ReportForm(request.POST, request.FILES)
        if form.is_valid():
            report = form.save(commit=False)
            if request.user.is_authenticated:
                report.reporter = request.user
                report.reporter_email = report.reporter_email or request.user.email
            if target_listing:
                report.listing = target_listing
            report.save()

            # Adminlərə bildiriş göndəririk (Ali və bütün adminlər)
            admin_users = User.objects.filter(Q(role='ADMIN') | Q(is_superuser=True))
            for admin in admin_users:
                try:
                    Notification.objects.create(
                        recipient=admin,
                        sender=request.user if request.user.is_authenticated else None,
                        notification_type='report',
                        title=f"⚠️ Yeni Xəta/Şikayət: {report.title}",
                        message=f"[{report.get_report_type_display()}] {report.description[:100]}... (Status: {report.get_status_display()})",
                        listing=report.listing
                    )
                except Exception:
                    pass

            messages.success(request, "Təşəkkür edirik! Xəta/şikayət bildirişiniz qeydə alındı və Supabase bazasına ötürüldü. Tezliklə araşdırılacaq.")

            if target_listing:
                return redirect("listing", listing_id=target_listing.id)
            return redirect(request.META.get('HTTP_REFERER', reverse('index')))
    else:
        initial_data = {}
        if request.user.is_authenticated:
            initial_data['reporter_email'] = request.user.email
        if target_listing:
            initial_data['listing'] = target_listing.id
            initial_data['title'] = f"Şikayət: {target_listing.title}"
            initial_data['report_type'] = 'fake_product'
        form = ReportForm(initial=initial_data)

    return render(request, "auctions/report.html", {
        "form": form,
        "target_listing": target_listing
    })


@login_required
def admin_reports_view(request):
    """Admin üçün xətaların və şikayətlərin idarəetmə siyahısı."""
    if not request.user.is_admin_user:
        messages.error(request, "Bu səhifə yalnız Administratorlar üçündür.")
        return redirect("index")

    status_filter = request.GET.get('status', '').strip()
    reports_qs = Report.objects.select_related('reporter', 'listing').all()
    if status_filter:
        reports_qs = reports_qs.filter(status=status_filter)

    return render(request, "auctions/admin_reports.html", {
        "reports": reports_qs,
        "status_filter": status_filter,
        "total_reports": reports_qs.count()
    })


# ==============================================================================
# CÜZDAN SİSTEMİ (BALANS ARTIRMA, NAĞDLAŞDIRMA VƏ TARİXÇƏ)
# ==============================================================================
@login_required
def wallet_view(request):
    """İstifadəçinin cüzdanı, balans artımı/çıxarışı və əməliyyat tarixçəsi."""
    user = request.user
    deposit_form = WalletDepositForm()
    withdraw_form = WalletWithdrawForm()

    if request.method == "POST":
        action = request.POST.get("action")

        # 1. Balansın artırılması (Top-up Deposit)
        if action == "deposit":
            deposit_form = WalletDepositForm(request.POST)
            if deposit_form.is_valid():
                amount = deposit_form.cleaned_data["amount"]
                card_num = deposit_form.cleaned_data["card_number"].replace(" ", "")
                card_last4 = card_num[-4:] if len(card_num) >= 4 else "0000"

                user.deposit_balance += amount
                user.save(update_fields=["deposit_balance"])

                import random
                auth_code = f"AUTH-{random.randint(100000, 999999)}"
                rrn = f"{timezone.now().strftime('%y%m%d')}{random.randint(100000, 999999)}"

                WalletTransaction.objects.create(
                    user=user,
                    transaction_type="DEPOSIT",
                    amount=amount,
                    balance_after=user.deposit_balance,
                    status="SUCCESS",
                    card_last_four=card_last4,
                    description=f"Kartla cüzdan balansının artırılması (*{card_last4}) [3D Secure - RRN: {rrn}]"
                )

                Notification.objects.create(
                    recipient=user,
                    notification_type="payment",
                    title="Cüzdan balansı artırıldı (3D Secure)",
                    message=f"Hesabınıza +{amount} ₼ vəsait mədaxil edildi. Təsdiq kodu: {auth_code}, RRN: {rrn}. Cari balansınız: {user.deposit_balance} ₼."
                )

                messages.success(request, f"Təbriklər! 3D Secure təsdiqi ilə {amount} ₼ məbləğində vəsait dərhal cüzdanınıza əlavə edildi (RRN: {rrn}).")
                return redirect("wallet")

        # 2. Balansdan çıxarış (Withdraw)
        elif action == "withdraw":
            withdraw_form = WalletWithdrawForm(request.POST)
            if withdraw_form.is_valid():
                amount = withdraw_form.cleaned_data["amount"]
                card_num = withdraw_form.cleaned_data["card_number"].replace(" ", "")
                card_last4 = card_num[-4:] if len(card_num) >= 4 else "0000"

                available_for_withdraw = user.get_available_balance()
                if amount > available_for_withdraw:
                    commitment = user.get_active_bids_commitment()
                    if commitment > Decimal('0.00'):
                        messages.error(request, f"Çıxarış Xətası: Aktiv hərraclarda lider olduğunuz təkliflər üçün {commitment} ₼ rezerv edilib. Hazırda yalnız sərbəst {available_for_withdraw} ₼ məbləğində vəsait çıxara bilərsiniz.")
                    else:
                        messages.error(request, f"Balansınızda kifayət qədər vəsait yoxdur. Cari balansınız: {user.deposit_balance} ₼.")
                else:
                    user.deposit_balance -= amount
                    user.save(update_fields=["deposit_balance"])

                    WalletTransaction.objects.create(
                        user=user,
                        transaction_type="WITHDRAW",
                        amount=-amount,
                        balance_after=user.deposit_balance,
                        status="SUCCESS",
                        card_last_four=card_last4,
                        description=f"Bank kartına nağdlaşdırma (*{card_last4})"
                    )

                    Notification.objects.create(
                        recipient=user,
                        notification_type="payment",
                        title="Vəsait çıxarışı təsdiqləndi",
                        message=f"*{card_last4} nömrəli karta {amount} ₼ köçürmə icra edildi. Qalan balansınız: {user.deposit_balance} ₼."
                    )

                    messages.success(request, f"{amount} ₼ məbləğində vəsait *{card_last4} nömrəli karta köçürüldü.")
                    return redirect("wallet")

    transactions = user.wallet_transactions.select_related('listing').all()[:50]
    total_deposited = user.wallet_transactions.filter(transaction_type="DEPOSIT", status="SUCCESS").aggregate(models.Sum('amount'))['amount__sum'] or Decimal('0.00')
    total_spent = user.wallet_transactions.filter(transaction_type="AUCTION_PAYMENT", status="SUCCESS").aggregate(models.Sum('amount'))['amount__sum'] or Decimal('0.00')
    total_earned = user.wallet_transactions.filter(transaction_type="AUCTION_EARNINGS", status="SUCCESS").aggregate(models.Sum('amount'))['amount__sum'] or Decimal('0.00')

    active_commitment = user.get_active_bids_commitment()
    available_balance = user.get_available_balance()
    leading_listings = user.get_active_leading_listings()

    return render(request, "auctions/wallet.html", {
        "deposit_form": deposit_form,
        "withdraw_form": withdraw_form,
        "transactions": transactions,
        "total_deposited": total_deposited,
        "total_spent": abs(total_spent),
        "total_earned": total_earned,
        "active_commitment": active_commitment,
        "available_balance": available_balance,
        "leading_listings": leading_listings,
    })


# ==============================================================================
# HƏRRAC QALİBİNİN SİFARİŞ VƏ ÖDƏNİŞ CHECKOUT SİSTEMİ
# ==============================================================================
@login_required
def checkout_view(request, listing_id):
    """Qazanılmış hərracın sifariş rəsmiləşdirilməsi, çatdırılma məlumatları və cüzdanla ödənişi."""
    product = get_object_or_404(Listing.objects.select_related('creator', 'winner'), pk=listing_id)
    highest_bid = product.bids.order_by('-amount').first()

    # Qalib, satıcı (ödənildikdə) və ya admin daxil ola bilər
    is_seller_viewing_paid = (product.creator == request.user and auction_result.payment_status == 'PAID')
    if product.winner != request.user and not request.user.is_admin_user and not is_seller_viewing_paid:
        messages.error(request, "Bu hərracın qalibi olmadığınız üçün ödəniş səhifəsinə daxil ola bilməzsiniz.")
        return redirect("listing", listing_id=product.id)

    auction_result, _ = AuctionResult.objects.get_or_create(
        listing=product,
        defaults={'winning_bid': highest_bid}
    )

    price = highest_bid.amount if highest_bid else product.starting_bid
    user = request.user

    # İlkin çatdırılma məlumatları (İstifadəçinin kimlik və məkan profilindən avtomatik gəlir)
    initial_data = {
        'delivery_name': f"{user.first_name} {user.last_name}".strip() or user.username,
        'delivery_phone': user.phone or "",
        'delivery_city': user.city or "Bakı",
        'delivery_address': user.address or "",
        'delivery_notes': auction_result.delivery_notes or "",
    }

    form = CheckoutOrderForm(initial=initial_data)

    if request.method == "POST":
        action = request.POST.get("action")

        # 1. Cüzdandan Ödəniş və ya Kartla Ödəniş
        if action in ["pay_wallet", "pay_card"]:
            form = CheckoutOrderForm(request.POST)
            if form.is_valid():
                delivery_name = form.cleaned_data['delivery_name']
                delivery_phone = form.cleaned_data['delivery_phone']
                delivery_city = form.cleaned_data['delivery_city']
                delivery_address = form.cleaned_data['delivery_address']
                delivery_notes = form.cleaned_data['delivery_notes']

                # İstifadəçinin profil məlumatlarını da yeniləyirik
                if not user.phone:
                    user.phone = delivery_phone
                if not user.city:
                    user.city = delivery_city
                if not user.address:
                    user.address = delivery_address
                user.save()

                # Kartla birbaşa ödənişdirsə, çatışmayan məbləği avtomatik cüzdana daxil edirik
                if action == "pay_card":
                    card_num = request.POST.get("card_number", "").replace(" ", "")
                    card_last4 = card_num[-4:] if len(card_num) >= 4 else "9999"
                    missing_amount = max(Decimal('0.00'), price - user.deposit_balance)
                    import random
                    rrn = f"{timezone.now().strftime('%y%m%d')}{random.randint(100000, 999999)}"
                    if missing_amount > 0:
                        user.deposit_balance += missing_amount
                        user.save(update_fields=['deposit_balance'])
                        WalletTransaction.objects.create(
                            user=user,
                            transaction_type='DEPOSIT',
                            amount=missing_amount,
                            balance_after=user.deposit_balance,
                            status='SUCCESS',
                            card_last_four=card_last4,
                            description=f"'{product.title}' sifarişi üçün 3D Secure kart mədaxili (*{card_last4}) [RRN: {rrn}]"
                        )

                # Cüzdan balansı yoxlanışı
                if user.deposit_balance < price:
                    messages.error(request, f"Cüzdanınızda kifayət qədər vəsait yoxdur. Tələb olunan: {price} ₼, Cüzdanınız: {user.deposit_balance} ₼. Zəhmət olmasa kartla birbaşa ödəyin və ya cüzdanınızı artırın.")
                    return render(request, "auctions/checkout.html", {
                        "product": product,
                        "highest_bid": highest_bid,
                        "auction_result": auction_result,
                        "price": price,
                        "form": form,
                    })

                # Ödənişi icra edirik:
                # 1. Alıcının cüzdanından çıxılır
                user.deposit_balance -= price
                # Etibarlılıq balı qalxır (+2% - maksimum 100%)
                user.reputation_score = min(Decimal('100.00'), user.reputation_score + Decimal('2.00'))
                user.save(update_fields=['deposit_balance', 'reputation_score'])

                # 2. Satıcının cüzdanına köçürülür
                seller = product.creator
                seller.deposit_balance += price
                seller.save(update_fields=['deposit_balance'])

                # 3. Əməliyyat tarixçəsi yazılır
                WalletTransaction.objects.create(
                    user=user,
                    transaction_type='AUCTION_PAYMENT',
                    amount=-price,
                    balance_after=user.deposit_balance,
                    status='SUCCESS',
                    listing=product,
                    description=f"'{product.title}' hərracının qalib ödənişi"
                )
                WalletTransaction.objects.create(
                    user=seller,
                    transaction_type='AUCTION_EARNINGS',
                    amount=price,
                    balance_after=seller.deposit_balance,
                    status='SUCCESS',
                    listing=product,
                    description=f"'{product.title}' hərrac satışından əldə olunan gəlir"
                )

                # 4. AuctionResult yenilənir
                auction_result.payment_status = 'PAID'
                auction_result.paid_at = timezone.now()
                auction_result.delivery_city = delivery_city
                auction_result.delivery_address = delivery_address
                auction_result.delivery_phone = delivery_phone
                auction_result.delivery_notes = delivery_notes
                auction_result.save()

                # 5. Bildirişlər göndərilir
                Notification.objects.create(
                    recipient=seller,
                    sender=user,
                    notification_type='payment',
                    title=f"'{product.title}' üçün ödəniş qəbul edildi!",
                    message=f"Alıcı {user.username} {price} ₼ ödənişi tamamladı və vəsait cüzdanınıza köçürüldü. Çatdırılma: {delivery_city}, {delivery_address} (Əlaqə: {delivery_phone}).",
                    listing=product
                )
                Notification.objects.create(
                    recipient=user,
                    notification_type='payment',
                    title=f"'{product.title}' ödənişi uğurla başa çatdı!",
                    message=f"{price} ₼ cüzdanınızdan ödənildi. Məhsul tezliklə qeyd etdiyiniz ünvana göndəriləcək. Etibarlılıq balınız artdı (+2%).",
                    listing=product
                )

                messages.success(request, f"Təbriklər! {price} ₼ ödəniş uğurla həyata keçirildi. Sifariş satıcıya yönləndirildi.")
                return redirect("checkout", listing_id=product.id)

        # 2. Sifarişdən İmtina (Cərimə & Etibarlılıq balının düşməsi!)
        elif action == "cancel_order":
            # Etibarlılıq balı 15% azaldılır ("etibarimizda dusmesin" qaydası)
            old_score = user.reputation_score
            user.reputation_score = max(Decimal('0.00'), user.reputation_score - Decimal('15.00'))
            user.save(update_fields=['reputation_score'])

            auction_result.payment_status = 'CANCELLED'
            auction_result.save()

            WalletTransaction.objects.create(
                user=user,
                transaction_type='PENALTY',
                amount=Decimal('0.00'),
                balance_after=user.deposit_balance,
                status='SUCCESS',
                listing=product,
                description=f"'{product.title}' hərracını qazandıqdan sonra ödənişdən imtina (Cərimə: Etibarlılıq balı -15%)"
            )

            Notification.objects.create(
                recipient=user,
                notification_type='lost',
                title="Sifarişdən imtina edildi (Etibarlılıq balınız azaldı)",
                message=f"'{product.title}' üçün ödənişdən imtina etdiyinizə görə etibarlılıq balınız {old_score}%-dən {user.reputation_score}%-ə endirildi.",
                listing=product
            )
            Notification.objects.create(
                recipient=product.creator,
                sender=user,
                notification_type='closed',
                title=f"Qalib '{product.title}' ödənişindən imtina etdi",
                message=f"Alıcı {user.username} məhsulun ödənişindən imtina etdi. Hərrac yenidən aktivləşdirilə bilər.",
                listing=product
            )

            messages.warning(request, f"Sifarişdən imtina edildi. Qaydaları pozduğunuz üçün etibarlılıq balınız 15% endirildi (Yeni etibarlılıq: {user.reputation_score}%).")
            return redirect("my_profile")

    return render(request, "auctions/checkout.html", {
        "product": product,
        "highest_bid": highest_bid,
        "auction_result": auction_result,
        "price": price,
        "form": form,
    })
