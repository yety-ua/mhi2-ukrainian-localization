# Virtual Cockpit: українська, версії та залізо / Ukrainian, software and hardware

Досліджено / Researched: **2026-10-13**. Scope: A4 B9, A5 F5, Q5 FY and Q7 4M
with the exact MHI2 K3346/MU1438 configuration required by this localization.
Firmware images and private vehicle scans are not distributed here.

## Українська

### Головний висновок

**Для A4/A5/Q5 AU491/0313 українська через цей пакет не працюватиме;
AU491/0379 має потрібні мовний код і власні українські ресурси.** Це підтверджено
аналізом штатних бінарників, повтореним 13.10.2026. Але наявність української в 0379
не означає, що 0379 можна без проблем встановити на будь-який VC.

**Для Q7 AU736/0310 українська через цей пакет не працюватиме; AU736/0378 і 0416
мають потрібну мовну карту й власні українські ресурси.** Після першої публікації
дослідження власник надав усі три пакети; їхній бінарний аналіз 13.10.2026 замінив
попередній статус «не встановлено» на ці визначені результати.

Наш SD-пакет встановлює мову **в MMI**, надсилає VC запит мови 43, але **не прошиває
VC і не переносить його мовні ресурси**. Для підтримуваного VC додатковий український
ресурсний пакет не потрібен: він має використати власний мовний банк.

### Таблиця програмних версій

| Моделі / сімейство | VC SW | Українська від нашого MMI | Доказ і практичний висновок |
| --- | --- | --- | --- |
| A4/A5/Q5, AU491 | **0313** | **Ні, у перевіреному штатному бінарнику** | BAP43 відхиляється; максимум таблиці — 29. Поточний MMI-пакет цього не виправляє |
| A4/A5/Q5, AU491 | **0379** | **Так на рівні ресурсів і протоколу** | BAP43 → внутрішній ID27; власні українські тексти. Фізичний показ і придатність оновлення перевіряються окремо |
| Q7, AU736 | **0310** | **Ні, у перевіреному бінарнику** | BAP43 відхиляється; максимум таблиці — 29; українських специфічних входжень немає |
| Q7, AU736 | **0378** | **Так на рівні ресурсів і протоколу** | BAP43 → ID27; 931 українське специфічне входження; фізичний показ і сумісність заліза окремо |
| Q7, AU736 | **0416** | **Так на рівні ресурсів і протоколу** | BAP43 → ID27; 943 українські специфічні входження; фізичний показ і сумісність заліза окремо |

Позначення «Так» для 0379 не є гарантією інсталяції на конкретне залізо.
Для інших AU491, зокрема 0299/0309/0373/0377/0417/0419, потрібен окремий аналіз:
з двох перевірених бінарників не випливає правило «всі нижче/вище номера X».

### Що саме перевірено у 0313 і 0379

Ланцюг: `uk_UA` у нашому MMI → `setMenuLanguage(43)` → мовна таблиця VC → його
власний UI. На 0313 ARM-функція повертає unsupported для 43. На 0379 та сама
категорія запиту має запис 43 → 27; нативний `bin/gtf2` містить українські тексти.
Повторний UTF-8 пошук літер Ґ/Є/І/Ї дає 0 входжень на 0313 та 931 на 0379.
Це допоміжний індикатор, не кількість усіх перекладів; вирішальний негативний доказ
0313 — відхилення коду 43. Шрифт в обох проаналізованих версіях уже підтримує українські літери.

[Перевірені хеші, адреси таблиць і результати](vc-binary-evidence.json).
Пакети: `AU_C1_AU491_0313_0991_prod_8S0906961AG_A4-A5-Q5_2017` і
`AU_C1_AU491_0379_1310_prod_8S0906961AL_A4-A5-Q5_2018`.
Заміна gtf2 або мовних кодів у 0313 не є готовим портом: потрібні сумісна таблиця
ресурсів і підтверджений спосіб встановлення зміненого підписаного образу.

### H15: українська та компас — різні питання

**Немає доказу, що сама H15 забороняє українську.** Є докази того, що окремі H15
працюють з 0379; питання — коректність усіх функцій і допустимість оновлення саме цього блока.

| Залізо AU491 / ситуація | Що відомо | Як це трактувати |
| --- | --- | --- |
| H11/H12 або нижче H15 | Тема оновлення попереджає про компас; є власницький звіт H12 із втратою компаса | Ризик за повідомленнями, не доведена неможливість запустити 0379 |
| **H15 + 0379** | **Суперечливі результати компаса** | Не позначати як гарантовано сумісну чи гарантовано несумісну |
| H17 + 0379 | Автор Matze89 описує власне успішне оновлення 0313 → 0379 з незмінним HW 8W5920790C | Конкретний польовий приклад; не гарантія для всіх part numbers |
| H18/H19 AU491 | У темах є згадки/запити, але цього недостатньо для нашої матриці приймання | Не робити автоматичний висновок «вище H15 — усе без проблем» |

У [власницьких повідомленнях #406/#407](https://www.digital-eliteboard.com/threads/virtual-cockpit-update-fuer-audi-a4-b9-audi-a5-f5-oder-audi-q5-fy.494687/page-28)
**spuerer, 25.01.2024** повідомляє, що H15/0379 зберігає компас;
**Alexooo, 30.01.2024** — що після оновлення H15 компас зник.
Це не контрольований тест однакових блоків/кодувань/режимів навігації.
Причину «інший компонент/немає драйвера» автор теми припускає, але ми бінарно її не довели.

[Початковий звіт Matze89 і застереження](https://www.digital-eliteboard.com/threads/virtual-cockpit-update-fuer-audi-a4-b9-audi-a5-f5-oder-audi-q5-fy.494687/)
та [H12-повідомлення](https://www.digital-eliteboard.com/threads/virtual-cockpit-update-fuer-audi-a4-b9-audi-a5-f5-oder-audi-q5-fy.494687/page-22?amp=1).
Надане власником посилання на page-26 теж переглянуте, але конкретні протилежні
повідомлення H15 розташовані на **page-28**, а не page-26.

Компас треба перевіряти без активного маршруту, зі штатною навігацією та з
CarPlay/Android Auto окремо. Перехід на паралельну карту/інший layout не є доказом,
що втрачений компас відновився. Спортовий layout також не доводить підтримку мови.

### Чому офіційний update не є універсальним

[Audi of America TSB 2052820/1, 01.11.2018](https://static.nhtsa.gov/odi/tsbs/2018/MC-10153134-9999.pdf)
розділяє модельні роки й part numbers. Його таблиця веде A4/A5/Q5 MY2017 до 0313,
MY2018 до 0379, Q7 MY2017 до 0310 і MY2018 до 0378. Для A4-подібної гілки там
вказані USA-блоки 8W5920890C/8W5920890G; для Q7 — 4M0920890B/4M0920890E.
Це не дозвіл на міжрічне оновлення EU-блока 8W5920790C/H15 і не документ про українську.

У метаданих наших AU491-пакетів є широкі variant/region checks. Прийняття пакета
інсталятором не доводить сумісність компаса, ECU-протоколу, комплектації чи recovery.
Зіставляти потрібно HW part number, SW part number, H-ревізію, software train,
модельний рік, регіон і комплектацію. Рік на кузові або лише H15 недостатні.

### Q7: що вдалося підтвердити та що лишилося відкритим

[Звіт власника Q7/SQ7, #16, 26.01.2024](https://www.digital-eliteboard.com/threads/audi-q7-4m-virtual-cockpit-update.527812/page-2)
вказує **VC 4M0920790C / H18 / 0378** та помилку відображення TPMS. У
[#10, 13.12.2023](https://www.digital-eliteboard.com/threads/audi-q7-4m-virtual-cockpit-update.527812/)
той самий власник зазначав, що дефект був і на попередній 0370. Тому некоректно
стверджувати, що 0378 обов'язково створює цю проблему або що вона спричинена мовою.

[Опис конкретного вживаного VC](https://www.naviservice.it/virtual-cockpit-audi-q7---quadro-strumenti-digitale-4m0920790d---271.000km/)
вказує **4M0920790D / H19 / SW0416**. Це власна інвентарна заява продавця;
мовна карта, український банк і придатність оновлення старого H15 з цього не випливають.

### Бінарна перевірка Q7 після отримання пакетів

Досліджені release `C1_AU736_0310_1001_prod`, `C1_AU736_0378_1280_prod` і
`C1_AU736_0416_1540_prod`. Внутрішній device каталог у всіх трьох —
**KI_FPK_AU536**; це фактичні метадані наданих AU736-пакетів, не помилка в назві.

| Перевірка | 0310 | 0378 | 0416 |
| --- | --- | --- | --- |
| Файли образів / перевірені SHA-1 блоки metainfo | 13 / 113 | 13 / 109 | 13 / 111 |
| Декодовані LZO блоки stage2 | 37 | 37 | 38 |
| imagefs checksum / межі файлів | Пройдено | Пройдено | Пройдено |
| Максимум BAP у native lookup | 29 | 43 | 43 |
| Результат коду 43 | -1, відхилено | 27 | 27 |
| Українські специфічні входження UTF-8 | 0 | 931 | 943 |
| Відсутні українські літери в штатному шрифті | Немає | Немає | Немає |

ELF у цих пакетах має урізані section headers, тому адреси мовних таблиць
перевіряли через **PT_LOAD program headers**. Для кожного бінарника знайдено
одну відповідну ARM-функцію lookup, перевірено її п'ять інструкцій та адресний літерал
і три прямі native BL-виклики. Мовна таблиця 0310 повністю збігається з AU491/0313;
таблиці 0378 і 0416 — з AU491/0379. Це прямий доказ протокольної підтримки,
окремий від форумних тверджень і номера версії.

Ресурси, хеші, адреси й кількість перевірених checksum-блоків збережені в
[vc-binary-evidence.json](vc-binary-evidence.json). Перевірка контрольних сум
доводить цілісність наданого набору, а не автентичність підпису або придатність
оновлення конкретного HW. Повідомлення про TPMS і H19/0416 вище лишаються
польовими/інвентарними даними, а не критеріями мовної підтримки.
Загальні оголошення «українізація Q7» без версії/заліза не використані як доказ.

### Які файли зі скріншота належать цьому дослідженню

Включені AU491/0313 і AU491/0379 для A4/A5/Q5 та AU736/0310, AU736/0378,
AU736/0416 для Q7. Номер після наступного підкреслення (0991/1310/1001/1280/1540)
не слід плутати з основною software release.

AU334 (TT), AU37X (A3), AU57X (A6/A7) і AU724 (R8) не входять у висновки для нашої
локалізації. Зокрема **8W6906961R не означає A4**: власницький
[A3-звіт](https://www.audiworld.com/forums/audi-a3-s3-rs-3-mkii-209/diy-virtual-cockpit-firmware-update-3067901/)
відносить AU37X/0150/0742 до KI_FPK_AU37X. Префікс номера носія/оновлення не є
надійним визначенням моделі. ASAM-ім'я EV_DashBoardAU736 теж зустрічається в A4-сканах;
потрібні повна ідентичність блока й метадані пакета.

**Рішення для користувача:** на AU491/0313 очікуйте українську в MMI, але не native VC;
на вже сумісному AU491/0379 очікується native українська VC з фізичною перевіркою.
H15-update потребує індивідуальної перевірки, зокрема компаса. Для Q7/0310
native української не буде; для сумісно встановлених Q7/0378 і 0416 мовна
підтримка підтверджена, з перевіркою показу на авто. Цей документ не додає
жодної VC-прошивки до нашої SD-карти.

## English

### Software-language result

| Models / family | VC software | Ukrainian from this MMI package | Evidence |
| --- | --- | --- | --- |
| A4/A5/Q5, AU491 | **0313** | **No in the inspected stock binary** | BAP43 rejected; maximum BAP table input 29 |
| A4/A5/Q5, AU491 | **0379** | **Supported in protocol/resources** | BAP43 → internal ID27; native Ukrainian bank; physical display and update eligibility remain separate |
| Q7, AU736 | **0310** | **No in the inspected binary** | BAP43 rejected; maximum table input 29; zero Ukrainian-specific occurrences |
| Q7, AU736 | **0378** | **Supported in protocol/resources** | BAP43 → ID27; 931 Ukrainian-specific occurrences; physical/HW checks separate |
| Q7, AU736 | **0416** | **Supported in protocol/resources** | BAP43 → ID27; 943 Ukrainian-specific occurrences; physical/HW checks separate |

The 0313/0379 native hashes and ARM lookup were rechecked on 2026-10-13.
UTF-8 Ukrainian-specific occurrences are 0 and 931 respectively, a corroborating
scan rather than a count of all translated slots. The decisive negative for 0313
is rejected BAP43. Both inspected fonts cover Ukrainian letters.
[Binary evidence](vc-binary-evidence.json). Other AU491 versions are not inferred
supported/unsupported merely from being numerically newer or older.

### Hardware and update boundaries

H15 is not a proven Ukrainian-language blocker. It is an update/functionality
uncertainty: [page-28 owner posts #406/#407](https://www.digital-eliteboard.com/threads/virtual-cockpit-update-fuer-audi-a4-b9-audi-a5-f5-oder-audi-q5-fy.494687/page-28)
report both retained and missing compass on H15/0379 (2024-01-25/30). The
[thread author's own H17 example](https://www.digital-eliteboard.com/threads/virtual-cockpit-update-fuer-audi-a4-b9-audi-a5-f5-oder-audi-q5-fy.494687/)
retains HW 8W5920790C while moving 0313 → 0379. Neither is universal approval.
Earlier H11/H12 compass-loss reports do not prove software cannot run; H18/H19
are not automatically guaranteed safe. A missing-driver explanation is a forum
claim, not a verified binary finding in this research.

Test compass without navigation, with native navigation and with phone navigation
separately. Parallel-map/sport-layout patches do not prove restored compass or
language support. Full part numbers, H revision, train, model year, region and
equipment matter; installer acceptance/skip checks do not prove compatibility.

[Audi TSB 2052820/1](https://static.nhtsa.gov/odi/tsbs/2018/MC-10153134-9999.pdf)
separates A4/A5/Q5 MY2017→0313, MY2018→0379 and Q7 MY2017→0310, MY2018→0378.
Its US cluster numbers differ from the inspected EU owner unit. It is a map-display
repair bulletin, not Ukrainian support evidence or blanket EU/H15 cross-year approval.

[Q7 owner post #16](https://www.digital-eliteboard.com/threads/audi-q7-4m-virtual-cockpit-update.527812/page-2)
identifies 4M0920790C/H18/0378 with TPMS display trouble. The same owner says
the issue existed on 0370 too; causation by 0378 or localization is unproven.
[A seller's own inventory](https://www.naviservice.it/virtual-cockpit-audi-q7---quadro-strumenti-digitale-4m0920790d---271.000km/)
identifies 4M0920790D/H19/0416 but does not verify its Ukrainian resources.
After the initial research publication, the owner supplied all three AU736 packages.
Their native inspection now confirms 0310 rejects BAP43, while 0378/0416 map it to
ID27 and contain Ukrainian text. All use package device KI_FPK_AU536. Metainfo
verification passes for 13 images each (113/109/111 SHA-1 blocks), with 37/37/38
decoded stage2 LZO blocks and validated imagefs. All inspected fonts cover Ukrainian.
Stripped ELF section tables required PT_LOAD address mapping. One matching lookup
and three direct BL callers were found per binary; Q7 tables match the corresponding
AU491 generations. [Hashes, addresses and verification counts](vc-binary-evidence.json).
Checksums establish consistency, not vendor signature authenticity or hardware eligibility.

Only AU491 and AU736 packages from the supplied screenshot enter this model scope.
TT/AU334, A3/AU37X, A6/A7/AU57X and R8/AU724 are excluded. In particular an
[A3 owner's AU37X/0150 account](https://www.audiworld.com/forums/audi-a3-s3-rs-3-mkii-209/diy-virtual-cockpit-firmware-update-3067901/)
uses update part 8W6906961R: an 8W prefix is not proof of an A4 target. A diagnostic
ASAM name alone is also insufficient. Build numbers and update-media part numbers
must not be mistaken for software release and physical cluster identity.

The M.I.B. SD overlay installs **MMI resources only** and requests menu language 43.
It never flashes VC, supplies a custom 0313 port or approves 0379 on arbitrary H15.
Language selection on a resource-capable VC and safe firmware deployment are distinct.
