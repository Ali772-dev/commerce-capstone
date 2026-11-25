-- ============================================================================
-- Layihə: Onlayn Açıq-Artırma Sistemi (Commerce Capstone)
-- Tədqiqat Mövzusu: PostgreSQL Hardening və Principle of Least Privilege
-- Müəlliflər: Əli Əliyev & Kərim Həsənov
-- Fənn: Verilənlər Bazasının İdarəetmə Sistemləri (VBİS)
-- Tarix: 2026-11-26
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. Tətbiq üçün Məhdud Səlahiyyətli İstifadəçi (Role) Yaradılması
-- Məqsəd: Superuser (postgres) ilə tətbiqin birbaşa qoşulmasının qarşısını almaq!
-- ----------------------------------------------------------------------------
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'auction_app_user') THEN
        CREATE ROLE auction_app_user WITH LOGIN PASSWORD 'SecureAppPass2026!';
    END IF;
END
$$;

-- ----------------------------------------------------------------------------
-- 2. İctimai Sxemdən Təhlükəli Standart İcazələrin Ləğvi (REVOKE)
-- ----------------------------------------------------------------------------
-- İctimaiyyətin bazada yeni cədvəl yaratmasını və bazaya ixtiyari girişi ləğv edirik
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON DATABASE commerce_db FROM PUBLIC;

-- Yalnız tətbiq istifadəçisinə bazaya qoşulmaq və sxemdən istifadə icazəsi verilir
GRANT CONNECT ON DATABASE commerce_db TO auction_app_user;
GRANT USAGE ON SCHEMA public TO auction_app_user;

-- ----------------------------------------------------------------------------
-- 3. Cədvəllər Üzrə İcazələrin Məhdudlaşdırılması (DML icazəsi, DDL qadağası)
-- Tətbiq istifadəçisinə YALNIZ SELECT, INSERT, UPDATE verilir. Heç vaxt DROP/TRUNCATE verilmir!
-- ----------------------------------------------------------------------------
GRANT SELECT, INSERT, UPDATE ON 
    auctions_listing, 
    auctions_bid, 
    auctions_comment, 
    auctions_watchlist, 
    auctions_category, 
    auctions_deposit, 
    auctions_wallettransaction, 
    auctions_notification 
TO auction_app_user;

-- DELETE icazəsi yalnız ləğv edilə bilən bəzi cədvəllərə verilir (məsələn, watchlist)
GRANT DELETE ON auctions_watchlist TO auction_app_user;

-- İstifadəçi cədvəlində Sütun Səviyyəli İcazə (Column-Level Grant):
-- Parol heşlərini və kritik sistem sahələrini qorumaq üçün:
GRANT SELECT (id, username, email, first_name, last_name, balance, is_seller, rating, phone_number, is_active, date_joined),
      UPDATE (first_name, last_name, balance, rating, phone_number)
      ON auctions_user TO auction_app_user;

-- Auto-increment ID-lərin (Sequence) işləməsi üçün:
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO auction_app_user;

-- ----------------------------------------------------------------------------
-- 4. PostgreSQL Sistem Kataloqunun (pg_catalog, pg_shadow) Qorunması
-- SQL Injection hücumlarında 'UNION SELECT ... FROM pg_shadow' və ya metadata sızmasını bloklamaq
-- ----------------------------------------------------------------------------
REVOKE SELECT ON pg_catalog.pg_shadow FROM PUBLIC;
REVOKE SELECT ON pg_catalog.pg_authid FROM PUBLIC;

-- ----------------------------------------------------------------------------
-- 5. Row-Level Security (RLS) Tətbiqi - Sətir Səviyyəli İzolyasiya
-- İstifadəçilər yalnız özlərinə aid balans və depozit qeydlərini görə bilsinlər!
-- ----------------------------------------------------------------------------
ALTER TABLE auctions_wallettransaction ENABLE ROW LEVEL SECURITY;
ALTER TABLE auctions_deposit ENABLE ROW LEVEL SECURITY;

-- Əgər əvvəlki siyasət varsa silinir və yenidən qurulur
DROP POLICY IF EXISTS user_own_transactions_policy ON auctions_wallettransaction;
CREATE POLICY user_own_transactions_policy ON auctions_wallettransaction
    FOR ALL
    USING (user_id = NULLIF(current_setting('app.current_user_id', true), '')::integer);

DROP POLICY IF EXISTS user_own_deposits_policy ON auctions_deposit;
CREATE POLICY user_own_deposits_policy ON auctions_deposit
    FOR ALL
    USING (user_id = NULLIF(current_setting('app.current_user_id', true), '')::integer);

-- RLS-dən yan keçilməməsi üçün tətbiq istifadəçisinə BYPASSRLS hüququ VERİLMİR!
ALTER ROLE auction_app_user NOBYPASSRLS;

-- ----------------------------------------------------------------------------
-- 6. Təhlükəsiz View (Görünüş) Yaradılması
-- İctimaiyyətə yalnız aktiv və təsdiqlənmiş məhsulları göstərən, daxili satıcı detallarını gizlədən View
-- ----------------------------------------------------------------------------
CREATE OR REPLACE VIEW public_active_listings_view AS
SELECT 
    l.id,
    l.title,
    l.description,
    l.current_price,
    l.buy_now_price,
    l.end_date,
    c.name AS category_name,
    u.username AS seller_username,
    u.rating AS seller_rating
FROM auctions_listing l
JOIN auctions_category c ON l.category_id = c.id
JOIN auctions_user u ON l.seller_id = u.id
WHERE l.is_active = TRUE;

GRANT SELECT ON public_active_listings_view TO auction_app_user;

-- ============================================================================
-- Nəticə: Tətbiq mühiti tam olaraq Principle of Least Privilege prinsipinə
-- uyğunlaşdırıldı. SQL Injection baş versə belə, hücumçu bazanı DROP/TRUNCATE
-- edə bilməz və digər istifadəçilərin şəxsi tranzaksiyalarını oxuya bilməz!
-- ============================================================================
