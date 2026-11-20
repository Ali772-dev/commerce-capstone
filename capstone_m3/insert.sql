-- ============================================================================
-- CAPSTONE LAYİHƏSİ – MƏRHƏLƏ 3
-- Layihənin Adı: Onlayn Açıq-Artırma və Hərrac İdarəetmə Sistemi (Online Auction Management System)
-- Fənn: Verilənlər Bazasının İdarəetmə Sistemləri (VBİS)
-- Fayl: insert.sql
-- Təsvir: Test və sınaq məlumatlarının daxil edilməsi.
--         Hər bir əsas cədvəldə minimum 10 qeyd təmin olunmuşdur.
-- ============================================================================

SET search_path TO auction_core, public;

-- ----------------------------------------------------------------------------
-- 1. USERS CƏDVƏLİ ÜÇÜN TEST MƏLUMATLARI (12 Qeyd)
-- Rollar: ADMIN, SELLER, BUYER; Statuslar: ACTIVE, BLOCKED
-- ----------------------------------------------------------------------------
INSERT INTO users (username, email, password_hash, phone, role, status, deposit_balance, reputation_score, created_at)
VALUES 
-- Administrator
('admin', 'admin@auctionhub.az', 'pbkdf2_sha256$600000$adminhash_sec_991', '+994 50 100 00 00', 'ADMIN', 'ACTIVE', 1000.00, 100.00, '2026-01-10 09:00:00+04'),

-- Satıcılar (Sellers)
('elmir_ramazanov', 'elmir.ramazanov@auctionhub.az', 'pbkdf2_sha256$600000$elmirhash_992', '+994 50 211 44 55', 'SELLER', 'ACTIVE', 1000.00, 98.50, '2026-01-15 10:30:00+04'),
('kerim_hasanov', 'kerim.hasanov@auctionhub.az', 'pbkdf2_sha256$600000$kerimhash_993', '+994 55 330 11 22', 'SELLER', 'ACTIVE', 1000.00, 95.00, '2026-01-16 11:15:00+04'),
('ali_aliyev', 'ali.aliyev@auctionhub.az', 'pbkdf2_sha256$600000$aliyevhash_994', '+994 50 909 77 88', 'SELLER', 'ACTIVE', 1000.00, 99.00, '2026-01-18 14:00:00+04'),
('rahman_islamzade', 'rahman.islamzade@auctionhub.az', 'pbkdf2_sha256$600000$rahmanhash_995', '+994 55 412 88 99', 'SELLER', 'ACTIVE', 1000.00, 97.00, '2026-01-20 16:45:00+04'),
('leyla_mammadova', 'leyla.m@auctionhub.az', 'pbkdf2_sha256$600000$leylahash_996', '+994 77 344 55 66', 'SELLER', 'ACTIVE', 1000.00, 96.00, '2026-02-01 12:00:00+04'),

-- Alıcılar (Buyers)
('ali_shukurlu', 'ali.shukurlu@auctionhub.az', 'pbkdf2_sha256$600000$alishukhash_997', '+994 70 882 19 01', 'BUYER', 'ACTIVE', 1000.00, 100.00, '2026-01-22 09:20:00+04'),
('rasim_xalilov', 'rasim.xalilov@auctionhub.az', 'pbkdf2_sha256$600000$rasimhash_998', '+994 51 644 33 22', 'BUYER', 'ACTIVE', 1000.00, 94.00, '2026-01-25 15:10:00+04'),
('nurlan_resulzade', 'nurlan.resulzade@auctionhub.az', 'pbkdf2_sha256$600000$nurlanhash_999', '+994 77 500 60 70', 'BUYER', 'ACTIVE', 1000.00, 92.50, '2026-01-28 17:30:00+04'),
('murad_qasimov', 'murad.q@auctionhub.az', 'pbkdf2_sha256$600000$muradhash_1001', '+994 50 771 22 33', 'BUYER', 'ACTIVE', 1000.00, 89.00, '2026-02-05 13:40:00+04'),
('aygun_tagizade', 'aygun.t@auctionhub.az', 'pbkdf2_sha256$600000$aygunhash_1002', '+994 55 889 00 11', 'BUYER', 'ACTIVE', 1000.00, 97.50, '2026-02-08 18:25:00+04'),

-- Qayda pozuntusuna görə bloklanmış istifadəçi (Constraint və Trigger testi üçün)
('kamran_bad_user', 'kamran.bad@auctionhub.az', 'pbkdf2_sha256$600000$badhash_1003', '+994 70 999 00 00', 'BUYER', 'BLOCKED', 0.00, 45.00, '2026-02-10 11:00:00+04');

-- ----------------------------------------------------------------------------
-- 2. CATEGORY CƏDVƏLİ ÜÇÜN TEST MƏLUMATLARI (10 Qeyd)
-- ----------------------------------------------------------------------------
INSERT INTO category (category_name, description)
VALUES 
('Elektronika və Qadjetlər', 'Smartfonlar, noutbuklar, planşetlər və digər müasir rəqəmsal avadanlıqlar'),
('Nəqliyyat və Avtomobillər', 'Minik avtomobilləri, motosikletlər, kommersiya nəqliyyatı və ehtiyat hissələri'),
('Zərgərlik və Saatlar', 'Orijinal lüks qol saatları, qızıl və brilyant zərgərlik məmulatları'),
('Kompüter və Proqramlaşdırma', 'Masaüstü kompüterlər, server avadanlıqları və proqramlaşdırma monitorları'),
('Məişət Texnikası və Ev', 'Ağıllı tozsoranlar, qəhvədəmləyənlər, soyuducular və iqlim texnikası'),
('Oyun və Əyləncə', 'Oyun konsolları, VR dəbilqələr, lisenziyalı oyun diskləri və kontrollerlər'),
('Dəb və Brend Geyim', 'Lüks brend geyimlər, dəri çantalar, ayaqqabılar və aksessuarlar'),
('İncəsənət və Antikvar', 'Rəsm əsərləri, tarixi sikkələr, xalçalar və nadir kolleksiya əşyaları'),
('Daşınmaz Əmlak', 'Mənzillər, bağ evləri, kommersiya obyektləri və torpaq sahələri'),
('İdman və Turizm', 'Velosipedlər, trenajorlar, düşərgə ləvazimatları və idman aksessuarları');

-- ----------------------------------------------------------------------------
-- 3. PRODUCT CƏDVƏLİ ÜÇÜN TEST MƏLUMATLARI (10 Qeyd)
-- ----------------------------------------------------------------------------
INSERT INTO product (seller_id, category_id, title, description, starting_price, current_price, min_increment, created_at, start_time, end_time, status)
VALUES 
-- 1. Aktiv: iPhone 15 Pro Max
(2, 1, 'Apple iPhone 15 Pro Max 256GB Natural Titanium', 'Rəsmi zəmanətli, ideal vəziyyətdə, batareya 100%. Qutusu və Type-C kabeli daxildir.', 150.00, 150.00, 10.00, '2026-11-18 10:00:00+04', '2026-11-18 10:00:00+04', '2026-11-25 18:00:00+04', 'ACTIVE'),

-- 2. Aktiv: BMW 530i M-Sport
(4, 2, 'BMW 530i M-Sport 2023 (Qara Metalik)', 'İmpromtex dilerindən alınıb, yürüş 14,000 km, bezkraska. Lazer faralar, Harman Kardon səs.', 5000.00, 5000.00, 100.00, '2026-11-19 12:00:00+04', '2026-11-19 12:00:00+04', '2026-11-26 15:00:00+04', 'ACTIVE'),

-- 3. Aktiv: Sony PlayStation 5 Slim
(5, 6, 'Sony PlayStation 5 Slim 1TB + 2 DualSense Pult', 'Bağlı qutuda, 1 il rəsmi zəmanət. Spider-Man 2 oyunu və əlavə Midnight Black kontroller.', 100.00, 100.00, 5.00, '2026-11-19 14:00:00+04', '2026-11-19 14:00:00+04', '2026-11-24 20:00:00+04', 'ACTIVE'),

-- 4. Aktiv: MacBook Pro 16 M3 Max
(3, 4, 'MacBook Pro 16" M3 Max 36GB / 1TB Space Black', '14-core CPU, 30-core GPU, 36GB vahid yaddaş, 1TB SSD. Batareya dövrü cəmi 24.', 300.00, 300.00, 20.00, '2026-11-18 16:30:00+04', '2026-11-18 16:30:00+04', '2026-11-25 21:00:00+04', 'ACTIVE'),

-- 5. Aktiv: Rolex Submariner Date
(4, 3, 'Rolex Submariner Date 126610LN Orijinal Saat', 'Oystersteel korpus, keramik bezel. Beynəlxalq sertifikatı və orijinal qutusu ilə.', 1200.00, 1200.00, 50.00, '2026-11-19 09:00:00+04', '2026-11-19 09:00:00+04', '2026-11-28 17:00:00+04', 'ACTIVE'),

-- 6. Aktiv: Dyson V15 Detect Absolute
(3, 5, 'Dyson V15 Detect Absolute Simsiz Tozsoran', 'Lazer başlıqlı ağıllı sensor, çox az işlənib, bütün aksessuarları və divar asılqanı yerindədir.', 80.00, 80.00, 5.00, '2026-11-20 08:00:00+04', '2026-11-20 08:00:00+04', '2026-11-22 22:00:00+04', 'ACTIVE'),

-- 7. Aktiv: Hermes Birkin 30 Dəri Çanta
(6, 7, 'Hermes Birkin 30 Togo Dəri Lüks Çanta (Qızılı Kilid)', 'Orijinal sənədləri və dustbag ilə. Paris butikindən alınıb, kolleksiya modeli.', 800.00, 800.00, 50.00, '2026-11-17 11:00:00+04', '2026-11-17 11:00:00+04', '2026-11-25 19:00:00+04', 'ACTIVE'),

-- 8. Aktiv: Trek Madone SLR 9 Yol Velosipedi
(2, 10, 'Trek Madone SLR 9 Karbon Şosse Velosipedi', 'Shimano Dura-Ace Di2 elektron ötürücü, OCLV 800 seriyalı karbon çərçivə, çəkisi 7.1 kq.', 400.00, 400.00, 25.00, '2026-11-18 15:00:00+04', '2026-11-18 15:00:00+04', '2026-11-26 12:00:00+04', 'ACTIVE'),

-- 9. Hərrac: Apple Watch Ultra 2 (İlkin olaraq başlanğıc qiymətlə aktiv, təkliflərdən sonra bağlanacaq)
(2, 1, 'Apple Watch Ultra 2 GPS + Cellular 49mm Titanium', 'Titan korpus, Sapphire şüşə, narıncı Ocean band. Hərrac yekunlaşıb və ödənilib.', 200.00, 200.00, 10.00, '2026-11-10 10:00:00+04', '2026-11-10 10:00:00+04', '2026-11-15 18:00:00+04', 'ACTIVE'),

-- 10. Hərrac: Sony WH-1000XM5 Qulaqlıq (İlkin olaraq aktiv, təkliflərdən sonra bağlanacaq)
(5, 1, 'Sony WH-1000XM5 Simsiz Səsboğucu Qulaqlıq', 'Sənaye lideri aktiv səsboğma, 30 saat batareya ömrü, gümüşü rəng.', 60.00, 60.00, 5.00, '2026-11-11 12:00:00+04', '2026-11-11 12:00:00+04', '2026-11-16 16:00:00+04', 'ACTIVE');

-- ----------------------------------------------------------------------------
-- 4. PRODUCT_IMAGE CƏDVƏLİ ÜÇÜN TEST MƏLUMATLARI (12 Qeyd)
-- ----------------------------------------------------------------------------
INSERT INTO product_image (product_id, image_url, sort_order)
VALUES 
(1, 'https://images.unsplash.com/photo-1695048133142-1a20484d2569?auto=format&fit=crop&w=800&q=80', 1),
(1, 'https://images.unsplash.com/photo-1510557880182-3d4d3cba35a5?auto=format&fit=crop&w=800&q=80', 2),
(2, 'https://images.unsplash.com/photo-1555215695-3004980ad54e?auto=format&fit=crop&w=800&q=80', 1),
(2, 'https://images.unsplash.com/photo-1580273916550-e323be2ae537?auto=format&fit=crop&w=800&q=80', 2),
(3, 'https://images.unsplash.com/photo-1606813907291-d86efa9b94db?auto=format&fit=crop&w=800&q=80', 1),
(4, 'https://images.unsplash.com/photo-1517336714731-489689fd1ca8?auto=format&fit=crop&w=800&q=80', 1),
(5, 'https://images.unsplash.com/photo-1522335789203-aabd1fc54bc9?auto=format&fit=crop&w=800&q=80', 1),
(6, 'https://images.unsplash.com/photo-1558317374-067fb5f30001?auto=format&fit=crop&w=800&q=80', 1),
(7, 'https://images.unsplash.com/photo-1584917865442-de89df76afd3?auto=format&fit=crop&w=800&q=80', 1),
(8, 'https://images.unsplash.com/photo-1485965120184-e220f721d03e?auto=format&fit=crop&w=800&q=80', 1),
(9, 'https://images.unsplash.com/photo-1579586337278-3befd40fd17a?auto=format&fit=crop&w=800&q=80', 1),
(10, 'https://images.unsplash.com/photo-1546435770-a3e426bf472b?auto=format&fit=crop&w=800&q=80', 1);

-- ----------------------------------------------------------------------------
-- 5. BID CƏDVƏLİ ÜÇÜN TEST MƏLUMATLARI (16 Qeyd)
-- Qeyd: trg_validate_and_place_bid triggeri hər təklifdən sonra product.current_price-ı
-- avtomatik sinxronlaşdırır!
-- ----------------------------------------------------------------------------
-- Məhsul 1 (iPhone 15 Pro Max) üzrə təkliflər
INSERT INTO bid (product_id, bidder_id, bid_amount, bid_time)
VALUES 
(1, 8, 160.00, '2026-11-18 11:00:00+04'),
(1, 7, 180.00, '2026-11-18 14:20:00+04'),
(1, 9, 210.00, '2026-11-19 09:40:00+04');

-- Məhsul 2 (BMW 530i) üzrə təklif
INSERT INTO bid (product_id, bidder_id, bid_amount, bid_time)
VALUES 
(2, 5, 5200.00, '2026-11-19 15:30:00+04');

-- Məhsul 3 (PlayStation 5) üzrə təkliflər
INSERT INTO bid (product_id, bidder_id, bid_amount, bid_time)
VALUES 
(3, 8, 105.00, '2026-11-19 16:00:00+04'),
(3, 9, 120.00, '2026-11-19 18:15:00+04'),
(3, 8, 125.00, '2026-11-19 18:16:00+04');

-- Məhsul 4 (MacBook Pro 16) üzrə təkliflər
INSERT INTO bid (product_id, bidder_id, bid_amount, bid_time)
VALUES 
(4, 9, 320.00, '2026-11-19 10:00:00+04'),
(4, 7, 360.00, '2026-11-19 13:45:00+04');

-- Məhsul 5 (Rolex Submariner) üzrə təkliflər
INSERT INTO bid (product_id, bidder_id, bid_amount, bid_time)
VALUES 
(5, 3, 1250.00, '2026-11-19 11:20:00+04'),
(5, 2, 1300.00, '2026-11-19 16:10:00+04');

-- Məhsul 6 (Dyson V15) üzrə təkliflər
INSERT INTO bid (product_id, bidder_id, bid_amount, bid_time)
VALUES 
(6, 8, 85.00, '2026-11-20 09:10:00+04'),
(6, 2, 95.00, '2026-11-20 11:30:00+04');

-- Məhsul 9 (Apple Watch Ultra 2 - Hərrac vaxtı bitməmişdən öncə verilmiş təkliflər)
INSERT INTO bid (product_id, bidder_id, bid_amount, bid_time)
VALUES 
(9, 8, 220.00, '2026-11-10 11:00:00+04'),
(9, 9, 250.00, '2026-11-12 15:30:00+04'),
(9, 7, 280.00, '2026-11-15 17:45:00+04'); -- Qalib Təklif (ID: 15)

-- Məhsul 10 (Sony WH-1000XM5 - Hərrac vaxtı bitməmişdən öncə verilmiş təkliflər)
INSERT INTO bid (product_id, bidder_id, bid_amount, bid_time)
VALUES 
(10, 11, 75.00, '2026-11-12 14:00:00+04'),
(10, 10, 110.00, '2026-11-16 15:50:00+04'); -- Qalib Təklif (ID: 17)

-- Təkliflər daxil edildikdən sonra 9 və 10 nömrəli hərracların statusunu CLOSED edirik
UPDATE product SET status = 'CLOSED' WHERE product_id IN (9, 10);

-- ----------------------------------------------------------------------------
-- 6. AUCTION_RESULT CƏDVƏLİ ÜÇÜN TEST MƏLUMATLARI (2 Qeyd)
-- Başa çatmış hərracların 1:1 qalibiyyət nəticələri
-- ----------------------------------------------------------------------------
INSERT INTO auction_result (product_id, winning_bid_id, closed_at)
VALUES 
(9, 15, '2026-11-15 18:00:00+04'),
(10, 17, '2026-11-16 16:00:00+04');

-- ----------------------------------------------------------------------------
-- 7. NOTIFICATION CƏDVƏLİ ÜÇÜN TEST MƏLUMATLARI (10 Qeyd)
-- İstifadəçilərə göndərilən bildirişlər (WON, LOST, OUTBID, NEW_BID)
-- ----------------------------------------------------------------------------
INSERT INTO notification (user_id, product_id, type, message, is_read, created_at)
VALUES 
(7, 9, 'WON', 'Təbriklər! Apple Watch Ultra 2 hərracını 280.00 ₼ təklifinizlə qazandınız!', TRUE, '2026-11-15 18:00:05+04'),
(9, 9, 'LOST', 'Apple Watch Ultra 2 hərracı başa çatdı. Digər iştirakçı daha yüksək təkliflə qalib oldu.', TRUE, '2026-11-15 18:00:05+04'),
(8, 9, 'LOST', 'Apple Watch Ultra 2 hərracı başa çatdı. Təəssüf ki, təklifiniz qalib gəlmədi.', TRUE, '2026-11-15 18:00:05+04'),
(10, 10, 'WON', 'Təbriklər! Sony WH-1000XM5 hərracını 110.00 ₼ təkliflə qazandınız!', FALSE, '2026-11-16 16:00:02+04'),
(11, 10, 'LOST', 'Sony WH-1000XM5 hərracı başa çatdı və digər alıcı qalib oldu.', TRUE, '2026-11-16 16:00:02+04'),
(8, 1, 'OUTBID', 'Apple iPhone 15 Pro Max elanında təklifiniz keçildi. Yeni lider təklif: 210.00 ₼', FALSE, '2026-11-19 09:40:02+04'),
(7, 1, 'OUTBID', 'Apple iPhone 15 Pro Max elanında Nurlan Rəsulzadə 210.00 ₼ təklif verərək lider oldu.', FALSE, '2026-11-19 09:40:02+04'),
(2, 1, 'NEW_BID', 'Məhsulunuza (iPhone 15 Pro Max) yeni 210.00 ₼ təklif verildi.', TRUE, '2026-11-19 09:40:03+04'),
(4, 2, 'NEW_BID', 'BMW 530i M-Sport avtomobilinizə 5200.00 ₼ təklif daxil oldu.', FALSE, '2026-11-19 15:30:05+04'),
(9, 3, 'OUTBID', 'PlayStation 5 Slim hərracında təklifiniz Rasim Xəlilov tərəfindən (125.00 ₼) keçildi.', FALSE, '2026-11-19 18:16:05+04');
