-- ============================================================================
-- CAPSTONE LAYİHƏSİ – MƏRHƏLƏ 3
-- Layihənin Adı: Onlayn Açıq-Artırma və Hərrac İdarəetmə Sistemi (Online Auction Management System)
-- Fənn: Verilənlər Bazasının İdarəetmə Sistemləri (VBİS)
-- Tələbə: Əli Əlizadə
-- Fayl: schema.sql
-- Təsvir: Verilənlər bazasının sxemi, cədvəllər, PK/FK/CHECK/UNIQUE məhdudiyyətləri,
--         təhlükəsizlik triggerləri və analitik VIEW-lər.
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. VERİLƏNLƏR BAZASININ YARADILMASI (Əmrlər şərh kimi təqdim olunur)
-- ----------------------------------------------------------------------------
-- CREATE DATABASE online_auction_db
--     WITH 
--     OWNER = postgres
--     ENCODING = 'UTF8'
--     LC_COLLATE = 'English_United States.1252'
--     LC_CTYPE = 'English_United States.1252'
--     TABLESPACE = pg_default
--     CONNECTION LIMIT = -1;

-- ----------------------------------------------------------------------------
-- BONUS 1: PostgreSQL Schema İstifadəsi
-- Məlumat təhlükəsizliyini və struktur təşkilatlanmanı təmin etmək üçün xüsusi sxem:
-- ----------------------------------------------------------------------------
CREATE SCHEMA IF NOT EXISTS auction_core;
SET search_path TO auction_core, public;

-- Mövcud cədvəllərin tərs ardıcıllıqla təmizlənməsi (təkrar icra oluna bilməsi üçün)
DROP VIEW IF EXISTS v_user_bidding_summary CASCADE;
DROP VIEW IF EXISTS v_auction_winners CASCADE;
DROP VIEW IF EXISTS v_active_auctions CASCADE;

DROP TABLE IF EXISTS notification CASCADE;
DROP TABLE IF EXISTS auction_result CASCADE;
DROP TABLE IF EXISTS bid CASCADE;
DROP TABLE IF EXISTS product_image CASCADE;
DROP TABLE IF EXISTS product CASCADE;
DROP TABLE IF EXISTS category CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- ----------------------------------------------------------------------------
-- 2. CƏDVƏLLƏRİN VƏ MƏHDUDİYYƏTLƏRİN (CONSTRAINTS) YARADILMASI
-- Məntiqi asılılıq ardıcıllığı: Valideyn (Parent) cədvəllərdən asılı (Child) cədvəllərə doğru
-- ----------------------------------------------------------------------------

-- CƏDVƏL 1: USERS (İstifadəçilər - Alıcı, Satıcı və Administratorlar)
CREATE TABLE users (
    user_id BIGINT GENERATED ALWAYS AS IDENTITY,
    username VARCHAR(50) NOT NULL,
    email VARCHAR(100) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    phone VARCHAR(20),
    role VARCHAR(20) NOT NULL DEFAULT 'BUYER',
    status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
    deposit_balance NUMERIC(12, 2) NOT NULL DEFAULT 0.00,
    reputation_score NUMERIC(5, 2) NOT NULL DEFAULT 100.00,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Məhdudiyyətlər (Constraints)
    CONSTRAINT pk_users PRIMARY KEY (user_id),
    CONSTRAINT uq_users_username UNIQUE (username),
    CONSTRAINT uq_users_email UNIQUE (email),
    CONSTRAINT chk_users_role CHECK (role IN ('ADMIN', 'SELLER', 'BUYER')),
    CONSTRAINT chk_users_status CHECK (status IN ('ACTIVE', 'BLOCKED')),
    CONSTRAINT chk_users_deposit_balance CHECK (deposit_balance >= 0.00),
    CONSTRAINT chk_users_reputation_score CHECK (reputation_score >= 0.00 AND reputation_score <= 100.00)
);

-- CƏDVƏL 2: CATEGORY (Məhsul Kateqoriyaları)
CREATE TABLE category (
    category_id INT GENERATED ALWAYS AS IDENTITY,
    category_name VARCHAR(50) NOT NULL,
    description TEXT,

    -- Məhdudiyyətlər (Constraints)
    CONSTRAINT pk_category PRIMARY KEY (category_id),
    CONSTRAINT uq_category_name UNIQUE (category_name)
);

-- CƏDVƏL 3: PRODUCT (Hərraca çıxarılan Məhsullar və Hərrac Şərtləri)
CREATE TABLE product (
    product_id BIGINT GENERATED ALWAYS AS IDENTITY,
    seller_id BIGINT NOT NULL,
    category_id INT NOT NULL,
    title VARCHAR(150) NOT NULL,
    description TEXT NOT NULL,
    starting_price NUMERIC(12, 2) NOT NULL,
    current_price NUMERIC(12, 2) NOT NULL,
    min_increment NUMERIC(12, 2) NOT NULL DEFAULT 1.00,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    start_time TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMPTZ NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',

    -- Məhdudiyyətlər (Constraints)
    CONSTRAINT pk_product PRIMARY KEY (product_id),
    CONSTRAINT fk_product_seller FOREIGN KEY (seller_id) 
        REFERENCES users(user_id) ON DELETE RESTRICT,
    CONSTRAINT fk_product_category FOREIGN KEY (category_id) 
        REFERENCES category(category_id) ON DELETE RESTRICT,
    CONSTRAINT chk_product_starting_price CHECK (starting_price > 0.00),
    CONSTRAINT chk_product_current_price CHECK (current_price >= starting_price),
    CONSTRAINT chk_product_min_increment CHECK (min_increment > 0.00),
    CONSTRAINT chk_product_status CHECK (status IN ('ACTIVE', 'CLOSED', 'CANCELLED')),
    CONSTRAINT chk_product_end_time CHECK (end_time > created_at),
    CONSTRAINT chk_product_start_end CHECK (end_time > start_time)
);

-- CƏDVƏL 4: PRODUCT_IMAGE (Məhsula aid Şəkillər - 1:N əlaqə)
CREATE TABLE product_image (
    image_id BIGINT GENERATED ALWAYS AS IDENTITY,
    product_id BIGINT NOT NULL,
    image_url VARCHAR(500) NOT NULL,
    sort_order INT NOT NULL DEFAULT 1,

    -- Məhdudiyyətlər (Constraints)
    CONSTRAINT pk_product_image PRIMARY KEY (image_id),
    CONSTRAINT fk_product_image_product FOREIGN KEY (product_id) 
        REFERENCES product(product_id) ON DELETE CASCADE,
    CONSTRAINT chk_product_image_sort_order CHECK (sort_order >= 1),
    CONSTRAINT uq_product_image_order UNIQUE (product_id, sort_order)
);

-- CƏDVƏL 5: BID (Hərrac Təklifləri və Dəyişməz Tarixçə - M:N əlaqənin həlli)
CREATE TABLE bid (
    bid_id BIGINT GENERATED ALWAYS AS IDENTITY,
    product_id BIGINT NOT NULL,
    bidder_id BIGINT NOT NULL,
    bid_amount NUMERIC(12, 2) NOT NULL,
    bid_time TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Məhdudiyyətlər (Constraints)
    CONSTRAINT pk_bid PRIMARY KEY (bid_id),
    CONSTRAINT fk_bid_product FOREIGN KEY (product_id) 
        REFERENCES product(product_id) ON DELETE RESTRICT,
    CONSTRAINT fk_bid_bidder FOREIGN KEY (bidder_id) 
        REFERENCES users(user_id) ON DELETE RESTRICT,
    CONSTRAINT chk_bid_amount CHECK (bid_amount > 0.00),
    CONSTRAINT uq_product_bid_amount UNIQUE (product_id, bid_amount)
);

-- CƏDVƏL 6: AUCTION_RESULT (Qalibiyyət Nəticəsi - 1:1 əlaqə)
CREATE TABLE auction_result (
    result_id BIGINT GENERATED ALWAYS AS IDENTITY,
    product_id BIGINT NOT NULL,
    winning_bid_id BIGINT NOT NULL,
    closed_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Məhdudiyyətlər (Constraints)
    CONSTRAINT pk_auction_result PRIMARY KEY (result_id),
    CONSTRAINT uq_auction_result_product UNIQUE (product_id),
    CONSTRAINT uq_auction_result_winning_bid UNIQUE (winning_bid_id),
    CONSTRAINT fk_result_product FOREIGN KEY (product_id) 
        REFERENCES product(product_id) ON DELETE RESTRICT,
    CONSTRAINT fk_result_winning_bid FOREIGN KEY (winning_bid_id) 
        REFERENCES bid(bid_id) ON DELETE RESTRICT
);

-- CƏDVƏL 7: NOTIFICATION (İstifadəçi Bildirişləri)
CREATE TABLE notification (
    notification_id BIGINT GENERATED ALWAYS AS IDENTITY,
    user_id BIGINT NOT NULL,
    product_id BIGINT NOT NULL,
    type VARCHAR(20) NOT NULL,
    message TEXT NOT NULL,
    is_read BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Məhdudiyyətlər (Constraints)
    CONSTRAINT pk_notification PRIMARY KEY (notification_id),
    CONSTRAINT fk_notification_user FOREIGN KEY (user_id) 
        REFERENCES users(user_id) ON DELETE RESTRICT,
    CONSTRAINT fk_notification_product FOREIGN KEY (product_id) 
        REFERENCES product(product_id) ON DELETE RESTRICT,
    CONSTRAINT chk_notification_type CHECK (type IN ('WON', 'LOST', 'OUTBID', 'NEW_BID'))
);

-- ----------------------------------------------------------------------------
-- 3. BONUS 3: BİZNES QAYDALARINI TƏMİN EDƏN TƏHLÜKƏSİZLİK TRİGGERLƏRİ
-- ----------------------------------------------------------------------------

-- Funksiya 1: Hərrac təklifinin biznes qaydalarını yoxlayan və qiyməti sinxronlaşdıran Trigger
CREATE OR REPLACE FUNCTION fn_validate_and_place_bid()
RETURNS TRIGGER AS $$
DECLARE
    v_seller_id BIGINT;
    v_product_status VARCHAR(20);
    v_end_time TIMESTAMPTZ;
    v_current_price NUMERIC(12, 2);
    v_min_increment NUMERIC(12, 2);
    v_last_bidder_id BIGINT;
    v_bidder_status VARCHAR(20);
BEGIN
    -- 1. Məhsul məlumatlarını əldə edirik
    SELECT seller_id, status, end_time, current_price, min_increment
    INTO v_seller_id, v_product_status, v_end_time, v_current_price, v_min_increment
    FROM product
    WHERE product_id = NEW.product_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Xəta: Təklif verilən məhsul tapılmadı! (ID: %)', NEW.product_id;
    END IF;

    -- 2. Təklif verən istifadəçinin statusunu yoxlayırıq
    SELECT status INTO v_bidder_status FROM users WHERE user_id = NEW.bidder_id;
    IF v_bidder_status = 'BLOCKED' THEN
        RAISE EXCEPTION 'Xəta: Bloklanmış istifadəçilər hərracda iştirak edə bilməz!';
    END IF;

    -- BR-2: Satıcı öz çıxardığı məhsula təklif verə bilməz
    IF NEW.bidder_id = v_seller_id THEN
        RAISE EXCEPTION 'Biznes Qaydası Pozuntusu (BR-2): Satıcı öz məhsuluna təklif verə bilməz!';
    END IF;

    -- BR-7: Vaxtı keçmiş və ya ləğv edilmiş hərraca təklif verilə bilməz
    IF v_product_status = 'CANCELLED' OR NEW.bid_time > v_end_time THEN
        RAISE EXCEPTION 'Biznes Qaydası Pozuntusu (BR-7): Hərrac aktiv deyil və ya təklif vaxtı bitib!';
    END IF;

    -- Mövcud təkliflərin sayını və son lider alıcını tapırıq
    SELECT bidder_id INTO v_last_bidder_id
    FROM bid
    WHERE product_id = NEW.product_id
    ORDER BY bid_amount DESC, bid_time ASC
    LIMIT 1;

    -- BR-8: Lider alıcı öz təklifinin üstünə arxa-arxaya yeni təklif verə bilməz
    IF v_last_bidder_id IS NOT NULL AND v_last_bidder_id = NEW.bidder_id THEN
        RAISE EXCEPTION 'Biznes Qaydası Pozuntusu (BR-8): Siz hazırda lider alıcısınız, ardıcıl təklif verə bilməzsiniz!';
    END IF;

    -- BR-4: Yeni təklif cari qiymətdən minimum artım addımı qədər çox olmalıdır
    IF v_last_bidder_id IS NULL THEN
        -- İlk təklif minimum başlanğıc qiymətinə bərabər və ya ondan böyük olmalıdır
        IF NEW.bid_amount < v_current_price THEN
            RAISE EXCEPTION 'Biznes Qaydası Pozuntusu (BR-4): İlk təklif başlanğıc qiymətdən (%) az ola bilməz!', v_current_price;
        END IF;
    ELSE
        IF NEW.bid_amount < (v_current_price + v_min_increment) THEN
            RAISE EXCEPTION 'Biznes Qaydası Pozuntusu (BR-4): Təklif cari qiymət + artım addımından (%) az ola bilməz!', (v_current_price + v_min_increment);
        END IF;
    END IF;

    -- Cari məhsulun qiymətini avtomatik yeniləyirik (Nəzarət olunan sinxronizasiya)
    UPDATE product
    SET current_price = NEW.bid_amount
    WHERE product_id = NEW.product_id;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_validate_and_place_bid
BEFORE INSERT ON bid
FOR EACH ROW
EXECUTE FUNCTION fn_validate_and_place_bid();

-- Funksiya 2: BR-6 Qaydası - Hərracın bitmə vaxtının dəyişdirilməsinin qadağan olunması
CREATE OR REPLACE FUNCTION fn_prevent_end_time_change()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.end_time IS DISTINCT FROM NEW.end_time AND OLD.status = 'ACTIVE' THEN
        RAISE EXCEPTION 'Biznes Qaydası Pozuntusu (BR-6): Hərracın bitmə vaxtı (end_time) dəyişdirilə bilməz!';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_prevent_end_time_change
BEFORE UPDATE ON product
FOR EACH ROW
EXECUTE FUNCTION fn_prevent_end_time_change();

-- ----------------------------------------------------------------------------
-- 4. BONUS 4: ANALİTİK VƏ HESABAT GÖRÜNÜŞLƏRİ (VIEWS)
-- ----------------------------------------------------------------------------

-- Görünüş 1: Aktiv Hərraclar və Statistik Göstəricilər
CREATE OR REPLACE VIEW v_active_auctions AS
SELECT 
    p.product_id,
    p.title AS product_name,
    c.category_name,
    u.username AS seller_name,
    p.starting_price,
    p.current_price,
    p.min_increment,
    p.start_time,
    p.end_time,
    ROUND(EXTRACT(EPOCH FROM (p.end_time - CURRENT_TIMESTAMP))/3600, 1) AS hours_remaining,
    COUNT(b.bid_id) AS total_bids,
    COALESCE(MAX(b.bid_amount), p.starting_price) AS highest_bid
FROM product p
JOIN category c ON p.category_id = c.category_id
JOIN users u ON p.seller_id = u.user_id
LEFT JOIN bid b ON p.product_id = b.product_id
WHERE p.status = 'ACTIVE' AND p.end_time > CURRENT_TIMESTAMP
GROUP BY p.product_id, p.title, c.category_name, u.username, p.starting_price, p.current_price, p.min_increment, p.start_time, p.end_time;

-- Görünüş 2: Yekunlaşmış Hərraclar və Qaliblərin Hesabatı
CREATE OR REPLACE VIEW v_auction_winners AS
SELECT 
    ar.result_id,
    p.product_id,
    p.title AS product_name,
    c.category_name,
    seller.username AS seller_name,
    winner.username AS winner_name,
    winner.email AS winner_email,
    winner.phone AS winner_phone,
    b.bid_amount AS winning_price,
    ar.closed_at
FROM auction_result ar
JOIN product p ON ar.product_id = p.product_id
JOIN category c ON p.category_id = c.category_id
JOIN users seller ON p.seller_id = seller.user_id
JOIN bid b ON ar.winning_bid_id = b.bid_id
JOIN users winner ON b.bidder_id = winner.user_id;

-- Görünüş 3: İstifadəçilərin Hərrac Aktivliyi və Cüzdan İcmalı
CREATE OR REPLACE VIEW v_user_bidding_summary AS
SELECT 
    u.user_id,
    u.username,
    u.role,
    u.deposit_balance,
    u.reputation_score,
    COUNT(DISTINCT b.product_id) AS participated_auctions_count,
    COUNT(b.bid_id) AS total_bids_placed,
    COUNT(DISTINCT ar.result_id) AS won_auctions_count
FROM users u
LEFT JOIN bid b ON u.user_id = b.bidder_id
LEFT JOIN auction_result ar ON b.bid_id = ar.winning_bid_id
GROUP BY u.user_id, u.username, u.role, u.deposit_balance, u.reputation_score;
