# Глибина локалізації / Localization depth

## Українська

**Висновок:** пакет широко інтегрує українську в A4 K3346: усі 22 цільові модулі,
вибір мови, клавіатура, конфігурація, діагностика й протокол запиту мови до кокпіта.
Він не обмежується перекладом головного меню. Водночас структурне покриття не означає
100% редакційної завершеності або перевірку кожного доступного екрана.

Аудит 20.10.2026 перевіряє **саме релізний ZIP**, SHA-256
`995440ea06cec135a37f53a4ac8fdff279b6e6d0d289e4d056738612fd4710b3`.
Машинний звіт: [resource-audit.json](resource-audit.json).

| Частина | Реалізовано | Що ще треба підтвердити |
| --- | --- | --- |
| Таблиці HMI | 22 модулі, 15 400 штатних непорожніх слотів + назва мови; 442 ZIP-записи, 418 таблиць; CRC/shape/flags/placeholders/round-trip проходять | Значення кожного перекладу, видимість і довгі написи на всіх екранах |
| Вибір мови | uk_UA, назва, прапорець, builtin config, 2D00 | Реальний запис і збереження після холодного запуску |
| Меню A4 | Штатні K3346 EvoHigh ресурси/ID; українське меню видно в емуляторі | Кожен пункт із реальною комплектацією |
| Клавіатура | Кирилиця за замовчуванням для uk_UA; 33 літери, Ґ Є І Ї, без Ё Ъ Ы Э; зміни в production lang_uk_hook.jar | Сама смуга, вибір символів і пошук на автомобілі |
| Рукописне введення | Java-шлях приймає українські літери; у попередньому локальному тесті прийнято друковані ҐЄІЇ | Рушій лишається ru_RU; це не доказ розпізнавання штрихів/курсиву. Потрібні тести всіх літер і кандидатів; російські літери можуть лишатися в репертуарі |
| Шрифти | Штатні шрифти підтримують Ґґ Єє Іі Її; для звичайного UI новий шрифт не потрібний | Апостроф U+02BC відсутній у попередньому аудиті; U+0027/U+2019 є. Контакти й введення перевіряються окремо |
| Навігація | Українські таблиці HMINavi; запит NAVI/TTS мов маршрутизується окремо | Реальні карти, український пошук адрес, POI, маршрути, вимова |
| Голос | Необов'язковий англійський fallback; окремий install/reboot цикл | Готовність NAVI/TTS/SDS, мікрофон, аудіо. Українського голосу/моделей немає |
| Connectivity | 9 статусних/термінологічних правок, зокрема видимість Bluetooth | Показ усіх цих станів на авто; не всі доступні в емуляторі |
| Редакційні правки 20.10.2026 | 95 слотів термінології («вказівка» → «повідомлення», «підказка», «сповіщення» тощо) 174 слоти перекладу в Navi, Media, Tuner, Online, Messaging, Phone, Settings 22 слоти формулювань меню («Ввести пункт призначення», «Дорожні повідомлення», «дозволити/уникати», «автоматично» тощо), 28 слотів «указати» → «вказати», 33 слоти «Ввести адресу» і 240 видимих німецьких/англійських назв у Navi, Media, Car, Online, Settings, Phone, Tuner 189 слотів, де скорочення розгорнуто в повні слова (разом 891 слот відносно попереднього релізу); німецькі голосові приклади замінено штатним англійським текстом; маніфести в [language-reviews-2026-10-20](language-reviews-2026-10-20/) | 69 термінологічних слотів, зокрема заголовок «Повідомлення» (12 символів) при ліміті слота 10–11, перевірено лише за кількістю символів; в емуляторі «Audi smartphone interface: Повідомле…» обрізається. Попап гучності показує «Гучність» (емулятор) |
| Virtual Cockpit | HMI просить мову 43; AU491/0379 та AU736/0378/0416 мають мовну карту й українські ресурси | AU491/0313 та AU736/0310 відхиляють BAP43. Фізичний показ, H15/компас, Q7/TPMS та update eligibility перевіряються окремо |
| SD-інсталятор | Перевірка точної цілі, baseline, CRC, hashes, read-back, SD/internal backup, recovery, journal | Справжній QNX/M.I.B./GEM, встановлення, відкат і робота без SD |

### Що означають залишкові кандидати

Після правок Connectivity і редакційних правок 20.10.2026 лишилося **6085 слотів без кирилиці**:
5022 дорівнюють англійському оригіналу, 1063 відрізняються. Це **не** 6085 пропущених перекладів:
сюди входять Bluetooth/CarPlay/Audi, числа, URL, географічні приклади, імена, діагностика
та підтримувані англійські команди голосової системи. Сам en_GB місцями містить німецьку,
тому рівність з en_GB теж не є доказом допустимості залишкового тексту.

Залишається редакційний перегляд підказок голосових команд у Media, Navi, Phone,
Messaging, Online, Tuner/TV, а також діагностичних і регіональних екранів. Потрібно
відрізняти український опис дії від англійської фрази, яку реально розпізнає SDS.
Приклад підтвердженого дефекту був `sichtbar/unsichtbar` у статусі Bluetooth; його
виправлено разом із сусідніми статусами. Перекладати всі некириличні рядки автоматично
не можна: це змінило б назви брендів і приклади підтримуваних команд.

Отже, **архітектурне покриття широке; редакційна повнота ще не сертифікована**.
Цей release candidate є зафіксованою відтворюваною версією для перевірки, а не
обіцянкою «100% фінальна українська в усіх функціях».

### Критерії завершення

1. Переглянути залишкові UI-кандидати за їхніми посиланнями й доступністю в A4 K3346;
   позначити: перекладено, підтримувана англійська команда, бренд/число або недоступний екран.
2. Пройти головне меню, Car/Settings, Radio/Media, Phone/Connectivity, повідомлення,
   навігацію та всі видимі діалоги/помилки на 1024×480; оцінити терміни й перенос рядків.
3. Перевірити українську смугу, всі літери/апострофи, адресний пошук і окремо HWR.
4. Виконати CHECK → INSTALL → холодний старт без SD → діагностика → RESTORE на цільовій
   голові, зберегти журнали й повторно звірити всі ресурси/датасети.
5. Окремо перевірити англійський voice fallback і фізичний VC; не змішувати ці результати з HMI.

## English

Детальна матриця VC та джерела / Detailed VC matrix and sources:
[VC_COMPATIBILITY.md](VC_COMPATIBILITY.md).

The localization integrates Ukrainian broadly across **all 22 A4 K3346 modules**,
language selection, the alphabet band, builtin/diagnostic configuration and the
cluster language request. It is not just a main-menu translation.

The released archive contains 15,400 nonempty target counterpart slots and one
additional language-name slot, 442 entries and 418 parsed string tables. CRC,
round-trip, target slot/flag/empty structure, formatting and placeholders pass.
Stock languages remain unchanged except the intended appended language name.
This does not establish semantic correctness or visual fit on every screen.

The production hook includes `I18NTarget`, `LanguageHandler`, the language-menu
mapping, `resources/atip.properties`, `TouchCharSetAndTTSHandler` and
`SpellerCharsetDefinitionEurope`. For uk_UA it defaults to Cyrillic and provides
all 33 Ukrainian letters without the four Russian-only letters in the band.
The native handwriting engine remains ru_RU. Printed-letter acceptance in an
earlier local input experiment is not finger-stroke or cursive recognition evidence.
The native repertoire can still include Russian-only handwriting candidates.

Native display fonts cover Ukrainian letters and ordinary/typographic apostrophes;
U+02BC was absent in the prior font audit. Imported contacts/input need independent
testing. Ukrainian navigation UI does not prove address search against installed maps.
Optional speech routing uses English resources and has no Ukrainian speech models.

The HMI requests cluster language 43. AU491/0313 rejects BAP43; AU491/0379 offline
mapping/resources are separate from physical rendering and safe update eligibility.
AU736/0310 also rejects BAP43; AU736/0378 and 0416 accept BAP43 and contain native
Ukrainian resources. Physical display and hardware/update eligibility remain separate.
The SD package never flashes the Virtual Cockpit.

After the nine Connectivity fixes and the 2026-10-20 editorial review (95 terminology
slots, 174 translated slots in Navi/Media/Tuner/Online/Messaging/Phone/Settings, 22 menu-wording slots, 28 "вказати" spelling slots, 33 "Enter Address" slots and 240 visible German/English labels 189 slots with abbreviations expanded to full words (891 slots in total against the previous release); German
voice examples replaced by the stock English text), **6085 non-Cyrillic slots remain as
candidates**, 5022 equal to English and 1063 different. 69 terminology slots, notably the
12-character "Повідомлення" for "Note" against a slot limit of 10-11 characters, were checked
by character count only; in the emulator the title "Audi smartphone interface: Повідомле…"
is truncated. These counts include product names, numbers,
URLs, examples, diagnostics and deliberate English speech commands. They are not
missing-translation counts or a completeness percentage. English tables themselves
contain some German text. Media/Navi/Phone/Messaging/Online/Tuner/TV voice-help contexts,
regional screens and engineering strings still need contextual editorial classification.

Completion requires an explicit classification of remaining reachable UI candidates,
a screen-by-screen terminology/layout review, alphabet/handwriting/address-search
acceptance and the exact-unit CHECK → INSTALL → cold boot without SD → diagnostic
inspection → RESTORE cycle. Actual voice and VC acceptance are separate.

The release is therefore a reproducible **preview**, with broad structural coverage,
not a certification of 100% editorial or physical-vehicle completeness.
