"""
============================================================================
Layihə: Onlayn Açıq-Artırma Sistemi (Commerce Capstone)
Mövzu: SQL İnyeksiyasının Anatomiyası: Zəif Sorğu vs Təhlükəsiz Müdafiə
Müəlliflər: Əli Əliyev & Kərim Həsənov
Fənn: Verilənlər Bazasının İdarəetmə Sistemləri (VBİS)
============================================================================
Bu skript Capstone layihəmizdə baş verə biləcək real SQL Injection hücumunu
və ona qarşı tətbiq etdiyimiz müdafiə mexanizmlərini (Prepared Statements,
Whitelisting və ORM) müqayisəli şəkildə nümayiş etdirir.
"""

import sys
import psycopg2

def connect_db():
    """PostgreSQL bazasına qoşulma köməkçisi"""
    try:
        conn = psycopg2.connect(
            dbname="commerce_db",
            user="postgres",
            password="password123", # və ya admin123 / cari konfiqurasiya
            host="127.0.0.1",
            port=5433
        )
        return conn
    except Exception as e:
        return None

# ============================================================================
# 1. ZƏİF KOD NÜMUNƏSİ (VULNERABLE CODE - STRING CONCATENATION)
# ============================================================================
def vulnerable_search(user_input: str):
    """
    TƏHLÜKƏLİ: İstifadəçi girişi birbaşa SQL sətrinə birləşdirilir (string concatenation).
    SQL Parser bu mətni kodun strukturu kimi qəbul edir.
    Sony Pictures (2011) hücumundakı eyni zəiflik modeli!
    """
    raw_query = f"SELECT id, title, current_price FROM auctions_listing WHERE is_active = TRUE AND title LIKE '%{user_input}%'"
    print(f"\n[!] GENERASİYA EDİLMİŞ ZƏİF SQL SORĞUSU:\n{raw_query}")
    return raw_query

# ============================================================================
# 2. HÜCUM PAYLOAD-U (SONY PICTURES 2011 CASE-STUDY MODELİ)
# ============================================================================
def simulate_attack():
    """
    Hücumçu axtarış sahəsinə UNION SELECT inyeksiyası daxil edir:
    Axtarış məhsul qaytarmalı olduğu halda, 'auctions_user' cədvəlindən
    istifadəçi adları, parollar və balansları çıxarır!
    """
    malicious_input = "' UNION SELECT id, username || ' | Pass: ' || password, balance FROM auctions_user --"
    print("=" * 70)
    print("SENARİ 1: SƏTİR BİRLƏŞDİRMƏSİ İLƏ SQL INJECTION HÜCUMU")
    print("=" * 70)
    print(f"Hücumçunun Girişi (Payload): {malicious_input}")
    
    injected_query = vulnerable_search(malicious_input)
    print("\n[!] TƏHLÜKƏ İZAHI:")
    print("SQL Parser sorğunu oxuyarkən tək dırnaq (') ilə sətri bağlayır və")
    print("UNION əmri ilə 'auctions_user' cədvəlini məhsul cədvəlinə calaq edir.")
    print("Nəticədə saytın axtarış nəticələrində istifadəçilərin parolları və balansları əks olunur!")


# ============================================================================
# 3. MÜDAFİƏ 1: PREPARED STATEMENTS (PARAMETRLİ SORĞULAR)
# ============================================================================
def secure_search_parameterized(user_input: str):
    """
    MÜDAFİƏ: Parametrli sorğu (Prepared Statement / %s yer tutucu).
    Verilənlər bazası mühərriki sorğunu (AST) ƏVVƏLCƏ analiz edir,
    istifadəçi girişini isə YALNIZ DƏYƏR (LITERAL DATA) kimi qəbul edir.
    Heç bir dırnaq və ya SQL açar sözü sorğu strukturunu dəyişə bilməz!
    """
    query = "SELECT id, title, current_price FROM auctions_listing WHERE is_active = TRUE AND title ILIKE %s"
    param = f"%{user_input}%"
    print("\n" + "=" * 70)
    print("SENARİ 2: PREPARED STATEMENTS (PARAMETRLİ SORĞU) İLƏ MÜDAFİƏ")
    print("=" * 70)
    print(f"Hazırlanmış Sorğu Şablonu: {query}")
    print(f"Ayrılmış Parametr: ({param},)")
    print("\n[+] MÜDAFİƏNİN İŞLƏMƏ PRİNSİPİ:")
    print("PostgreSQL mühərrikində SQL Parser şablonu bir dəfə parse edir.")
    print("İstifadəçi girişi (hətta dırnaq və UNION olsa belə) bütöv sətir kimi axtarılır.")
    print("İnyeksiya qeyri-mümkündür!")


# ============================================================================
# 4. MÜDAFİƏ 2: DİNAMİK 'ORDER BY' ÜÇÜN WHITELISTING
# ============================================================================
def secure_dynamic_sorting(sort_by_input: str, direction_input: str):
    """
    PARAMETRLİ SORĞULAR KİFAYƏT ETMƏYƏN HALLAR:
    SQL standartında sütun adları, cədvəl adları və ya ASC/DESC sözləri
    parametrləşdirilə BİLMƏZ (%s burada işləmir).
    Həll: STRICT WHITELISTING (Ağ Siyahı Yoxlanışı).
    """
    print("\n" + "=" * 70)
    print("SENARİ 3: DİNAMİK 'ORDER BY' VƏ WHITELISTING MÜDAFİƏSİ")
    print("=" * 70)
    
    # İcazə verilən sütunların ağ siyahısı (Allowed Whitelist)
    ALLOWED_SORT_FIELDS = {
        "price": "current_price",
        "date": "created_at",
        "title": "title",
        "id": "id"
    }
    ALLOWED_DIRECTIONS = {"asc": "ASC", "desc": "DESC"}

    # 1. Sütun yoxlanışı
    clean_sort = ALLOWED_SORT_FIELDS.get(sort_by_input.lower(), "created_at")
    
    # 2. İstiqamət yoxlanışı
    clean_dir = ALLOWED_DIRECTIONS.get(direction_input.lower(), "DESC")

    # Yalnız təsdiqlənmiş təhlükəsiz dəyərlər SQL-ə daxil edilir
    safe_query = f"SELECT id, title, current_price FROM auctions_listing ORDER BY {clean_sort} {clean_dir}"
    print(f"İstifadəçinin verdiyi daxilolma: sort='{sort_by_input}', dir='{direction_input}'")
    print(f"Whitelisting sonrası təhlükəsiz SQL: {safe_query}")
    print("\n[+] Əgər hücumçu 'price; DROP TABLE auctions_bid;--' göndərsə belə,")
    print("ağ siyahıda tapılmadığı üçün avtomatik 'created_at DESC' seçilir.")


# ============================================================================
# 5. MÜDAFİƏ 3: DJANGO ORM SƏVİYYƏSİ
# ============================================================================
def secure_django_orm_demonstration():
    """
    Capstone layihəmizdə tətbiq etdiyimiz Django ORM yanaşması:
    Listing.objects.filter(is_active=True, title__icontains=q).order_by(clean_sort)
    Avtomatik olaraq PostgreSQL parametrli sorğusuna çevrilir.
    """
    print("\n" + "=" * 70)
    print("SENARİ 4: CAPSTONE LAYİHƏMİZDƏ TƏTBİQ OLUNAN DJANGO ORM QORUMASI")
    print("=" * 70)
    print("Kod: Listing.objects.filter(is_active=True, title__icontains=user_query)")
    print("Django ORM bütün axtarış girişlərini avtomatik %s ilə bağlayır və")
    print("xüsusi simvolları zərərsizləşdirir (escape edir).")


if __name__ == "__main__":
    print("**********************************************************************")
    print("  CAPSTONE VBİS TƏDQİQAT İŞİ: SQL INJECTION ANATOMİYASI VƏ MÜDAFİƏ  ")
    print("  Müəlliflər: Əli Əliyev & Kərim Həsənov                            ")
    print("**********************************************************************")
    simulate_attack()
    secure_search_parameterized("' UNION SELECT id, username, balance FROM auctions_user --")
    secure_dynamic_sorting("price; DROP TABLE auctions_bid;--", "desc")
    secure_django_orm_demonstration()
    print("\n[V] Bütün test ssenariləri uğurla nümayiş etdirildi.")
