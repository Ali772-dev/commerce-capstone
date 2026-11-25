# SQL İnyeksiyasının Anatomiyası, Real Case-Study Təhlili və Capstone Layihələrə Tətbiqi
## Komanda Tədqiqat İşi üzrə 12–15 Dəqiqəlik Təqdimat Nitqi, Praktiki Təlimat və Sual-Cavab Bələdçisi

> **Fənn:** Verilənlər Bazasının İdarəetmə Sistemləri (VBİS)  
> **Komanda Üzvləri:**  
> 1. **Kərim Həsənov** — Tədqiqatçı 1 (Nəzəriyyə) & Tədqiqatçı 2 (Case Study)  
> 2. **Əli Əliyev** — Tətbiq Memarı (Capstone Uyğunlaşdırma) & Baza İnzibatçısı (PostgreSQL DBA)  
> **Capstone Layihəsi:** Onlayn Açıq-Artırma və Hərrac Sistemi (*Commerce* — Django + PostgreSQL 18)  
> **Təqdimat Vaxtı:** 12–15 dəqiqə çıxış + 3 dəqiqə sual-cavab  

---

## 1. Zaman Bölgüsü və Komanda Rol Xəritəsi (Time Management)

| Slayd | Mövzu | Təqdimatçı | Müddət |
| :--- | :--- | :--- | :--- |
| **Slayd 1** | Titul, Giriş və Komanda Təqdimatı | Kərim & Əli | **1.0 dəqiqə** |
| **Slayd 2** | SQL Parser, AST və SQLi Növlərinin Anatomiyası | Kərim Həsənov | **1.5 dəqiqə** |
| **Slayd 3** | İkinci Dərəcəli SQLi və Prepared Statements Müdafiəsi | Kərim Həsənov | **1.5 dəqiqə** |
| **Slayd 4** | Case Study: Sony Pictures (2011) Hücum Vektoru | Kərim Həsənov | **1.5 dəqiqə** |
| **Slayd 5** | Sony Hadisəsinin Kök Səbəb Təhlili və Baza Dərsləri | Kərim Həsənov | **2.0 dəqiqə** |
| **Slayd 6** | Capstone Layihəmizdə Risk Xəritəsi və Həssas Əməliyyatlar | Əli Əliyev | **1.5 dəqiqə** |
| **Slayd 7** | Hücum və Müdafiə Modelləşdirməsi: "Əvvəl vs Sonra" | Əli Əliyev | **2.0 dəqiqə** |
| **Slayd 8** | PostgreSQL Hardening: Least Privilege və DDL Qadağası | Əli Əliyev | **1.5 dəqiqə** |
| **Slayd 9** | Row-Level Security (RLS), Təhlükəsiz View və AI Şəffaflığı | Əli Əliyev | **1.5 dəqiqə** |
| **Slayd 10**| Nəticə, Sual-Cavab Sessiyası (Q&A) və İstinadlar | Kərim & Əli | **0.5 dəqiqə** |
| **Q&A** | Müəllim və Auditoriyanın Suallarının Cavablandırılması | Hər iki iştirakçı | **3.0 dəqiqə** |
| **CƏMİ** | | | **14–15 dəqiqə** |

---

## 2. Slayd-bə-Slayd Təqdimatçı Nitqi (Word-for-Word Script)

### Slayd 1: Titul və Giriş (00:00 – 01:00)
- **Kərim Həsənov:**  
  *"Hörmətli müəllim və tələbə yoldaşlarımız, hər birinizi salamlayırıq. Bu gün komandamız — mən Kərim Həsənov və həmkarım Əli Əliyev, Verilənlər Bazasının İdarəetmə Sistemləri fənni üzrə tədqiqat işimizi təqdim edirik. Mövzumuz: 'SQL İnyeksiyasının Anatomiyası, Real Case-Study Təhlili və Capstone Layihələrə Tətbiqi'."*
- **Əli Əliyev:**  
  *"Tədqiqatımızın əsas məqsədi SQL inyeksiyasını təkcə nəzəri səviyyədə deyil, verilənlər bazası mühərrikinin sorğu emalı mərhələsində necə formalaşdığını araşdırmaq, tarixə düşmüş Sony Pictures 2011 hadisəsini təhlil etmək və nəhayət, bu zəifliyi semestr ərzində qurduğumuz Onlayn Açıq-Artırma (Commerce) layihəmizin PostgreSQL bazasında modelləşdirərək çoxqatlı müdafiə sistemini qurmaqdır. İndi isə sözü nəzəri tədqiqat üçün Kərimə verirəm."*

---

### Slayd 2: SQL İnyeksiyasının Mexanizmi və Təsnifatı (01:00 – 02:30)
- **Kərim Həsənov:**  
  *"Tədqiqatımızın birinci mərhələsində SQL İnyeksiyasının verilənlər bazası mühərriki daxilində yaranma mexanizmini araşdırdıq.  
  Tətbiqdən verilənlər bazasına sorğu daxil olduqda, ilk olaraq **SQL Parser** işə düşür. Parser sorğunu leksik və sintaktik təhlil edərək **Abstrakt Sintaksis Ağacı (AST - Abstract Syntax Tree)** formalaşdırır. Bu ağacda əmrlər (məsələn, SELECT, WHERE) operator qovşaqları kimi, istifadəçi girişləri isə yarpaq qovşaqlar (Literal Data) kimi təsnif olunur.  
  Boşluğun fundamental kökü **Sətir Birləşdirməsi (String Concatenation)** zamanı yaranır. Tərtibatçı istifadəçi girişini yoxlamadan SQL sətrinə calaq etdikdə, hücumçunun daxil etdiyi tək dırnaq (') simvolu və SQL açar sözləri parser tərəfindən məlumat kimi deyil, birbaşa sintaksis operatoru kimi qəbul olunur və AST strukturunu tamamilə dəyişir.  
  
  Biz SQL inyeksiyalarını 3 əsas kateqoriyaya böldük:  
  1. **In-band SQLi:** Hücumçu nəticəni daxil olduğu kanal vasitəsilə alır. Bura xəta mesajlarından informasiya sızdıran *Error-based* və iki sorğunu birləşdirən *UNION-based* daxildir.  
  2. **Inferential / Blind SQLi:** Ekrana heç bir baza xətası çıxmadıqda tətbiq olunur. *Boolean-based* yanaşmada True/False cavablarına əsasən, *Time-based* yanaşmada isə PostgreSQL-in `pg_sleep()` funksiyasının yaratdığı gecikmələrə görə məlumat bit-bit oxunur.  
  3. **Out-of-band SQLi:** Baza birbaşa hücumçuya cavab verə bilmədikdə, DNS və ya HTTP sorğuları vasitəsilə məlumat kənara sızdırılır."*

---

### Slayd 3: İkinci Dərəcəli SQLi və Prepared Statements Müdafiəsi (02:30 – 04:00)
- **Kərim Həsənov:**  
  *"Növbəti kritik tədqiqat sualımız **İkinci Dərəcəli SQL İnyeksiyasıdır (Second-Order SQLi)**. Klassik inyeksiyadan fərqli olaraq, burada zərərli payload daxil olduğu an bazanı sındırmır. Əksinə, bazaya tamamilə qanuni məlumat kimi daxil olur və saxlanılır (Stored). Təhlükə onda yaranır ki, başqa bir arxa plan prosesi və ya hesabat generasiyası həmin qeydi bazadan oxuyub İKİNCİ bir dinamik sorğuya qoşur. Bu zaman partlayış baş verir. İkinci dərəcəli SQLi daha təhlükəlidir, çünki Veb Tətbiq Qoruma Divarları (WAF) ilkin girişdə heç bir zərərli davranış görmür və tərtibatçılar bazadakı verilənə artıq 'təhlükəsiz' kimi etibar edirlər.  
  
  Müdafiə tərəfində isə qızıl standart **Prepared Statements (Parametrli sorğulardır)**. PostgreSQL mühərrikində parametrli sorğu işlədildikdə, SQL Parser sorğunun strukturunu əvvəlcədən tərtib edir və icra planını (Query Execution Plan) dondurur. İstifadəçi girişi ayrıca protokol səviyyəsində göndərilir və nə daxil edilirsə edilsin, mühərrik onu YALNIZ DƏYƏR kimi qəbul edir.  
  
  Lakin parametrli sorğuların çatmadığı hallar var: SQL standartına görə dinamik `ORDER BY` istiqamətləri (ASC/DESC), cədvəl və sütun adları parametr qəbul etmir ($1 qoymaq sintaksis xətasıdır). Bu zaman komandamız **Strict Whitelisting (Ağ Siyahı)** tətbiq etmişdir. Yalnız icazə verilən sahələrin lüğəti qəbul olunur, kənar girişlər avtomatik təmizlənir."*

---

### Slayd 4: Case Study — Sony Pictures Entertainment (2011) Hücumu (04:00 – 05:30)
- **Kərim Həsənov:**  
  *"İkinci mərhələdə püşkatma mövzusu olaraq dünya kiber-təhlükəsizlik tarixinin ən səs-küylü hadisələrindən birini — **Sony Pictures Entertainment (2011)** hücumunu dərindən araşdırdıq.  
  2011-ci ilin mayında LulzSec qruplaşması heç bir mürəkkəb Zero-day boşluğu olmadan, sadəcə ictimai veb interfeysdəki yoxlanılmamış URL parametrini istismar edərək Sony-nin daxili bazasını ələ keçirdi.  
  Hücumun texniki vektoru sadə bir `UNION-based SQL Injection` idi. Hücumçular:  
  `UNION SELECT 1, column_name, ... FROM information_schema.columns`  
  sorğusunu icra edərək bazadakı bütün cədvəllərin siyahısını aldılar və nəticədə 1 milyondan çox istifadəçinin şəxsi məlumatlarını (adlar, doğum tarixləri, e-maillər, şifrələr) saniyələr içində sızdırdılar.  
  
  Baza səviyyəsindəki ən böyük skandal isə o idi ki, Sony kimi nəhəng korporasiya istifadəçi şifrələrini bazada **AÇIQ MƏTN (PLAIN-TEXT)** şəklində saxlayırdı! Heç bir heşləmə (MD5, SHA, bcrypt) və duzlama (salt) aparılmamışdı. Baza oxunan kimi parollar dərhal internetə düşdü."*

---

### Slayd 5: Sony Hadisəsinin Kök Səbəb Təhlili və Baza Dərsləri (05:30 – 07:30)
- **Kərim Həsənov:**  
  *"Sony hadisəsinin kök səbəblərini təhlil edərkən 3 fundamental memarlıq səhvi aşkar etdik:  
  1. **Kod Səviyyəsində:** İstifadəçi girişinin sanitarizasiya olunmadan birbaşa SQL sorğusuna birləşdirilməsi.  
  2. **Baza Dizaynında:** Parolların və həssas məlumatların kriptoqrafik heşləmə olmadan plain-text saxlanılması.  
  3. **İcazə Bölünməsində:** Veb tətbiqin qoşulduğu istifadəçinin həddindən artıq yüksək hüquqlara sahib olması. Tək bir müsabiqə səhifəsi bütün korporativ istifadəçi cədvəlini oxumaq icazəsinə malik idi.  
  Bu zəncirvari fəsadlar Sony-yə 171 milyon dollardan çox birbaşa ziyan vurdu və PlayStation şəbəkəsi həftələrlə dayandı.  
  
  PostgreSQL mühitində bu fəlakətin qarşısını almaq üçün:  
  - Parollar `pgcrypto` və ya tətbiq qatında güclü Argon2 / PBKDF2 ilə heşlənməlidir.  
  - Veb tətbiqinə yalnız lazımi cədvəllər üzrə minimum icazə verilməlidir.  
  - Sütun səviyyəli icazə (Column-Level Grant) ilə `password` sütununun oxunması adi istifadəçilərə qadağan edilməlidir.  
  İndi isə bu dərslərin öz Capstone layihəmizə necə tətbiq edildiyini nümayiş etdirmək üçün sözü Tətbiq Memarımız Əli Əliyevə verirəm."*

---

### Slayd 6: Capstone Layihəmizdə Risk Xəritəsi və Həssas Əməliyyatlar (07:30 – 09:00)
- **Əli Əliyev:**  
  *"Çox sağ ol, Kərim. Mən semestr boyu hazırladığımız Onlayn Açıq-Artırma (Commerce) layihəmizin relyasion sxemini və PostgreSQL arxitekturasını təhlil edərək ən kritik 3 istifadəçi əməliyyatının Risk Xəritəsini çıxardım:  
  1. **Axtarış və Dinamik Filtrləmə:** `auctions_listing` cədvəlində `title`, `category` və `order_by` sahələri. Əgər axtarış sorğusu sətir birləşdirməsi ilə yazılarsa, Sony Pictures hadisəsindəki kimi `UNION SELECT` inyeksiyası ilə hücumçu birbaşa `auctions_user` cədvəlinə sıçraya bilər.  
  2. **Giriş və Autentifikasiya:** `auctions_user` cədvəlində `username` və `password`. Klassik `' OR 1=1 --` inyeksiyası ilə şifrə bilmədən administrator hesabına daxil olmaq və hərrac qaydalarını pozmaq riski mövcuddur.  
  3. **Hərrac Təklifləri və Pul Kisəsi Tranzaksiyaları:** `auctions_bid` və `auctions_wallettransaction` cədvəlləri. Beh depoziti və balans çıxarışlarında İkinci dərəcəli (Second-Order) SQLi vasitəsilə rəqiblərin gizli avto-təkliflərini (auto-bid) oxumaq və balansı saxtalaşdırmaq təhlükəsi var."*

---

### Slayd 7: Hücum və Müdafiə Modelləşdirməsi — "Əvvəl vs Sonra" (09:00 – 11:00)
- **Əli Əliyev:**  
  *"Layihəmizin real cədvəlləri üzərində bu hücumu və müdafiəni canlı modelləşdirdik:  
  
  **ƏVVƏL (Zəif Kod və Hücum):**  
  Təsəvvür edin ki, `views.py` faylında axtarış belə yazılıb:  
  `SELECT id, title, current_price FROM auctions_listing WHERE title LIKE '%" + q + "%'`  
  Hücumçu axtarış qutusuna Sony Pictures modelindəki bu payload-u daxil edir:  
  `' UNION SELECT id, username || ' | ' || password, balance FROM auctions_user --`  
  SQL Parser tək dırnaqla `title` şərtini qapayır və `UNION` vasitəsilə bütün `auctions_user` cədvəlini məhsul siyahısına calaq edir. Nəticədə saytın axtarış pəncərəsində məhsul əvəzinə bütün qeydiyyatdan keçmiş istifadəçilərin istifadəçi adları, heşlənmiş şifrələri və balansları açıq şəkildə sıralanır!  
  
  **SONRA (Təhlükəsiz Kod və Whitelisting):**  
  Biz layihəmizdə bu boşluğu tamamilə aradan qaldırdıq:  
  1. Axtarış üçün Django ORM-in parametrləşdirilmiş sorğusundan istifadə etdik:  
     `Listing.objects.filter(is_active=True, title__icontains=q)` — bu sorğu PostgreSQL mühərrikinə `%s` yer tutucusu ilə gedir və inyeksiya qeyri-mümkün olur.  
  2. Dinamik `ORDER BY` üçün ciddi **Whitelisting** funksiyası yazdıq. `ALLOWED_SORTS = {'price': 'current_price', 'date': 'created_at'}` lüğəti qurduq. Əgər kimsə `price; DROP TABLE auctions_bid;--` göndərsə belə, ağ siyahıda tapılmadığı üçün sistem avtomatik təhlükəsiz `created_at DESC` seçir və zərərli kod icra olunmur."*

---

### Slayd 8: PostgreSQL Hardening və Least Privilege (11:00 – 12:30)
- **Əli Əliyev:**  
  *"İndi isə məsələnin ən fundamental hissəsinə — Verilənlər Bazası Səviyyəsində İzolyasiyaya keçirik.  
  Tətbiq kodunda səhv olsa belə, verilənlər bazası sonuncu qala kimi özünü qorumalıdır. Bunun üçün hazırladığımız `hardening.sql` skriptində **Ən Az Səlahiyyət Prinsipini (Principle of Least Privilege)** tətbiq etdik:  
  
  1. **Superuser Qadağası:** Tətbiq heç vaxt `postgres` (superuser) hesabı ilə qoşulmur. Yalnız məhdud hüquqlu `auction_app_user` rolu yaradıldı.  
  2. **İcazələrin Ləğvi (REVOKE):** `REVOKE CREATE ON SCHEMA public FROM PUBLIC;` və `REVOKE ALL ON DATABASE commerce_db FROM PUBLIC;` əmrləri ilə ictimai icazələr sıfırlandı.  
  3. **DDL Qadağası (DROP / TRUNCATE):** `auction_app_user` roluna YALNIZ DML (SELECT, INSERT, UPDATE) hüquqları verildi. Tətbiq istifadəçisinə heç bir halda `DROP`, `TRUNCATE` və ya `ALTER` icazəsi VERİLMİR! Haker hətta SQLi tapsa belə, `DROP TABLE` icra edə bilməz və icazə xətası (Permission Denied) alacaq.  
  4. **Sistem Kataloqlarının Qorunması:** Hakerlərin `information_schema` və ya `pg_shadow` cədvəllərindən istifadəçi heşlərini çəkməməsi üçün `pg_catalog.pg_shadow` və `pg_authid` cədvəllərinə oxuma hüququ ləğv edildi."*

---

### Slayd 9: Row-Level Security (RLS), Təhlükəsiz View və AI Şəffaflığı (12:30 – 14:00)
- **Əli Əliyev:**  
  *"Baza təhlükəsizliyini ən yüksək səviyyəyə çatdırmaq üçün iki qabaqcıl mexanizm tətbiq etdik:  
  
  1. **Row-Level Security (RLS) — Sətir Səviyyəli Təhlükəsizlik:**  
     `auctions_wallettransaction` və `auctions_deposit` cədvəllərində RLS aktivləşdirildi:  
     `CREATE POLICY user_own_transactions_policy ON auctions_wallettransaction FOR ALL USING (user_id = current_setting('app.current_user_id')::int);`  
     Bu o deməkdir ki, hücumçu bazada hətta `SELECT * FROM auctions_wallettransaction` icra etsə belə, PostgreSQL mühərriki yalnız həmin sessiyaya aid sətirləri qaytarır! Digər istifadəçilərin balans hərəkətləri mühərrik səviyyəsində bloklanır.  
  2. **Təhlükəsiz View:** `public_active_listings_view` yaradaraq satıcıların telefon nömrəsi və daxili rekvizitlərini ictimai sorğulardan təcrid etdik.  
  
  **AI Şəffaflıq Bəyannaməmiz:**  
  Tapşırığın tələbinə uyğun olaraq açıq bəyan edirik ki, tədqiqat zamanı sintaktik analiz və konseptual sxemlərin yoxlanılmasında süni intellekt alətlərindən köməkçi kimi istifadə edilmişdir. Lakin təqdim olunan bütün zəif sorğular, `UNION SELECT` payload-ları və PostgreSQL `hardening.sql` skriptləri komandamız tərəfindən yerli `PostgreSQL 18` və `Commerce` mühitində icra edilmiş, hər bir icazə və məhdudiyyət canlı olaraq test edilib təsdiqlənmişdir."*

---

### Slayd 10: Yekun və Sual-Cavaba Keçid (14:00 – 14:30)
- **Kərim Həsənov:**  
  *"Yekun olaraq qeyd edirik ki, kiber-təhlükəsizlik təkcə veb tərtibatçının deyil, həm də verilənlər bazası inzibatçısının birgə məsuliyyətidir. Əsl təhlükəsizlik tək bir qatda deyil, **Dərinlikdə Müdafiə (Defense-in-Depth)** fəlsəfəsində — yəni WAF, Prepared Statements, PostgreSQL Least Privilege və Row-Level Security-nin vahid vəhdətində təmin olunur."*
- **Əli Əliyev:**  
  *"Diqqətiniz üçün hər birinizə təşəkkür edirik! İndi isə böyük məmnuniyyətlə müəllimimizin və tələbə yoldaşlarımızın suallarını cavablandırmağa hazırıq."*

---

## 3. Müəllimin Verə Biləcəyi 5 Kritik İmtahan Sualı və Qızıl Akademik Cavablar

### Sual 1: "Siz dediniz ki, Prepared Statements istifadə edirik. Bəs nə üçün dinamik ORDER BY-da parametr (%s və ya $1) işləmir?"
- **Cavab (Əli Əliyev):**  
  *"Çox sağ olun, müəllim, bu çox fundamental bir sualdır. SQL qrammatikasına görə Prepared Statements yalnız **DƏYƏRLƏRİ (Literal Data)** parametrləşdirə bilir. Sütun adları (`current_price`), cədvəl adları və çeşidləmə istiqamətləri (`ASC` / `DESC`) isə SQL qrammatikasında identifikator və sintaktik operator hesab olunur. Əgər biz `ORDER BY $1` yazsaq, baza onu `ORDER BY 'current_price'` kimi qəbul edəcək, yəni sütuna görə deyil, sabit bir mətnə görə çeşidləyəcək və ya sintaksis xətası verəcək. Məhz buna görə də identifikatorlar üçün Prepared Statement işləmir və yeganə düzgün elmi həll **Strict Whitelisting (Ağ Siyahı)** tətbiq etməkdir."*

---

### Sual 2: "İkinci Dərəcəli (Second-Order) SQL İnyeksiyası WAF-ı necə aldadır və niyə klassik SQLi-dən daha təhlükəlidir?"
- **Cavab (Kərim Həsənov):**  
  *"Müəllim, klassik SQLi-də hücumçu zərərli payload-u göndərən kimi tətbiq dərhal həmin sorğunu icra edir və WAF (Web Application Firewall) paket daxilindəki şübhəli tək dırnaqları və SQL açar sözlərini filtr edib bloklaya bilir.  
  İkinci dərəcəli SQLi-də isə hücumçu məsələn, qeydiyyatdan keçərkən adını `admin'--` qoyur. İlkin qeydiyyat sorğusu parametrləşdirildiyi üçün bazaya zərərsiz bir sətir kimi qeyd olunur. Təhlükə aylar sonra baş verir: məsələn, admin panelində istifadəçilərin hesabatı generasiya olunarkən tərtibatçı bazadan həmin adı oxuyur və 'bu artıq bizim bazadadır, deməli təhlükəsizdir' zənni ilə dinamik sorğuya calayır. Nəticədə hücum tətbiqin öz daxilindən, etibarlı mənbədən başlayır və bütün WAF-lardan yan keçir."*

---

### Sual 3: "Sony Pictures hadisəsindəki ən böyük baza dizaynı səhvi nə idi və PostgreSQL-də bunu necə aradan qaldırdınız?"
- **Cavab (Kərim Həsənov):**  
  *"Sony Pictures hadisəsində ən bağışlanmaz səhv istifadəçi parollarının bazada **açıq mətn (plain-text)** saxlanılması və tətbiqin bazaya bütün sxemi oxumaq hüququ olan tək bir hesab ilə qoşulması idi.  
  Biz öz PostgreSQL mühitimizdə:  
  1. Bütün parolları duzlanmış güclü heş (PBKDF2/Argon2) ilə saxlayırıq.  
  2. Tətbiq roluna (`auction_app_user`) `auctions_user` cədvəlindən parolları oxumağı məhdudlaşdıran **Column-Level Grant** tətbiq etdik. Yəni tətbiq axtarış və ya profil göstərərkən şifrə sütununa çıxış əldə edə bilməz."*

---

### Sual 4: "Əgər haker yenə də tətbiqdə SQL inyeksiyası taparsa, sizin PostgreSQL Least Privilege konfiqurasiyanız bazanı necə qoruyacaq?"
- **Cavab (Əli Əliyev):**  
  *"Əla sualdır, müəllim. Bu, tam olaraq bizim 'Dərinlikdə Müdafiə' konsepsiyamızdır.  
  Təsəvvür edin ki, gələcəkdə hansısa yeni tərtibatçı səhv edib zəif bir sorğu yazdı və hücumçu `'; DROP TABLE auctions_listing; --` göndərdi.  
  Bizim yaratdığımız `auction_app_user` roluna `hardening.sql` skriptimizdə YALNIZ `SELECT`, `INSERT`, `UPDATE` hüququ verilib. Heç bir `DROP`, `TRUNCATE` və ya `ALTER` hüququ yoxdur. PostgreSQL mühərriki sorğunu icra etməyə cəhd edən kimi `ERROR: permission denied for table auctions_listing` xətası verəcək və cədvəl toxunulmaz qalacaq. Eyni zamanda hücumçu `pg_shadow` cədvəlinə müraciət etsə belə, `REVOKE` etdiyimiz üçün digər sistem istifadəçilərinin məlumatlarını görə bilməyəcək."*

---

### Sual 5: "Row-Level Security (RLS) nədir və niyə adi 'WHERE user_id = current_user' şərtindən daha üstündür?"
- **Cavab (Əli Əliyev):**  
  *"Adi `WHERE user_id = 5` şərti tətbiq kodunda (Python/Django) yazılır. Əgər tərtibatçı həmin WHERE şərtini yazmağı unudarsa və ya SQL inyeksiyası ilə `OR 1=1` edilərsə, bütün istifadəçilərin şəxsi məlumatları ifşa olur.  
  Row-Level Security (RLS) isə tətbiqdən asılı olmayan, **birbaşa verilənlər bazası mühərrikində** çalışan məcburi təhlükəsizlik siyasətidir. Tətbiqdən hansı sorğunun gəlməsindən asılı olmayaraq, PostgreSQL daxili səviyyədə avtomatik olaraq yalnız cari sessiyanın `user_id`-sinə aid sətirləri qaytarır. Haker `SELECT * FROM auctions_wallettransaction` yazsa belə, baza ona digər insanların balansını göstərməkdən fiziki olaraq imtina edir."*

---

## 4. Təqdimat Faylları və Sənədlər Qovluğu

Bütün fayllar layihənin qovluğunda hazırdır:
1. **PowerPoint Təqdimatı:** [`capstone_m3/SQLi_Anatomy_Capstone_Presentation.pptx`](file:///c:/Users/AliAL/OneDrive/Desktop/Commerce/capstone_m3/SQLi_Anatomy_Capstone_Presentation.pptx)  
2. **PostgreSQL Təhlükəsizlik Skripti:** [`capstone_m3/hardening.sql`](file:///c:/Users/AliAL/OneDrive/Desktop/Commerce/capstone_m3/hardening.sql)  
3. **Canlı Zəiflik və Müdafiə Demo Kodu:** [`capstone_m3/sqli_demo.py`](file:///c:/Users/AliAL/OneDrive/Desktop/Commerce/capstone_m3/sqli_demo.py)  
4. **Nitq və Müdafiə Bələdçisi:** [`capstone_m3/Presentation_Speech_and_Defense_Guide.md`](file:///c:/Users/AliAL/OneDrive/Desktop/Commerce/capstone_m3/Presentation_Speech_and_Defense_Guide.md)  
