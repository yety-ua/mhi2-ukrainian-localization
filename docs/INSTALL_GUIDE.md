# Покрокова інструкція для першого встановлення / First-time install guide

[Українська](#українська) · [English](#english) · [← README](../README.md)

## Українська

Ця інструкція — для тих, хто робить це **вперше** і не знайомий з M.I.B. Вона нічого не
замінює в [README](../README.md): там коротко, тут — кожен крок із поясненням, що ви маєте
побачити і що робити, якщо бачите інше.

### Спершу чесно

- Пакет має статус **preview**. Його перевірено на комп'ютері й в емуляторі, але **ще ніхто не
  встановлював його на справжній автомобіль**. Ви серед перших. Це нормально, але
  ризик реальний: помилка під час запису може залишити магнітолу, яка не завантажується.
- Пакет **не перепрошиває** магнітолу, лише замінює мовні файли й один параметр. Усе, що
  він змінює, спершу копіюється, а `RESTORE` повертає оригінал.
- **Якщо вам страшно або немає запасного входу (див. Етап 5) — зупиніться на Етапі 4
  (`CHECK`).** Він нічого не змінює і вже корисний: показує, чи підходить вам пакет.

### Словник

<details>
<summary>Показати пояснення термінів (GEM, SD1, MMX…)</summary>

| Слово | Що це |
| --- | --- |
| **MMI / голова / магнітола** | Блок з екраном у машині (head unit). Тут усе про нього. |
| **M.I.B.** | Безкоштовний набір скриптів ([Mr-MIBonk](https://github.com/Mr-MIBonk/M.I.B._More-Incredible-Bash)), що живе на SD-карті й запускається з прихованого меню блока. Наш пакет працює **через** нього. |
| **GEM** | Green Engineering Menu — приховане сервісне меню блока. Там з'являється пункт `m.i.b.`, коли M.I.B. встановлено, а SD-карту вставлено. |
| **SD1** | Перший слот для SD-карти в блоці (другий — SD2). Карта з M.I.B. має стояти саме в SD1. |
| **ACTION.txt** | Один файл на карті з одним словом. Це «перемикач» пакета: `CHECK` (перевірити), `INSTALL` (встановити), `RESTORE` (відновити). |
| **CHECK** | Режим «тільки подивитись». Нічого не встановлює й не змінює мову. |
| **telnet / порт 23** | Запасний вхід у магнітолу з ноутбука по мережі. Потрібен лише на випадок, якщо після встановлення блок не запустить меню. |
| **MMX** | Назва частини блока, де лежать мовні файли. Telnet на порту 23 відкриває саме її. |
| **Лог** | Текстовий файл `uk-localization/logs/run-….log` на карті; там написано, що саме сталося. |

</details>

### Загальний план

| Етап | Що робите | Чи змінює авто |
| --- | --- | --- |
| 1 | Перевіряєте, чи підходить вам пакет | ні |
| 2 | Перевіряєте, що M.I.B. уже працює | ні |
| 3 | Готуєте SD-карту на комп'ютері | ні |
| 4 | Запускаєте пункт GEM: `CHECK` (крок 1 із 3) | **ні** |
| 5 | Страховка: запасний вхід, бекап, живлення | створює копії |
| 6 | Запускаєте той самий пункт ще **двічі** (чеклист, потім `INSTALL`) | **так** |
| 7 | Перезавантаження й перевірка | — |

### Що потрібно мати

- SD-карта **FAT32**, яка вже використовується з M.I.B. (рекомендуємо до 32 ГБ, без захисту
  від запису — перемикач збоку карти у положенні «відкрито»).
- Комп'ютер з кардрідером.
- Автомобіль із **MMI K3346 / MU1438** (Етап 1) і вже встановленим **M.I.B.** (Етап 2).
- Для страховки (Етап 5): ноутбук із Windows, USB-Ethernet адаптер, який магнітола
  розпізнає, і мережевий кабель; щоб блок не вимкнувся під час запису — зовнішнє живлення
  автомобіля (зарядний пристрій / підтримка живлення на час діагностики).
  Запуск двигуна **не замінює** підтримку живлення.
- Час без поспіху. Під час запису не можна виймати карту, натискати Back і вимикати запалювання.

### Етап 1. Чи підходить вам пакет

Пакет працює **лише** з прошивкою `MHI2_ER_AUG22_K3346`, MU `1438`, HMI
`HMI_AU_MIB2_H_EU_G22_C6_190300`. Інші версії інсталятор **відхилить сам** — це безпечно.

Охоплені моделі (за цією прошивкою): **A4, A5, Q5, Q7**. **Не підтримуються:** A3
(будь-яка), TT, R8, A6/A7 та інші MMI, навіть якщо їхні комбінації для GEM схожі.

Подивитись версію заздалегідь можна в налаштуваннях MMI (зазвичай Налаштування → обслуговування
системи → інформація про версію; назви залежать від вашого авто), або просто запустити
`CHECK` на Етапі 4: він перевірить усе сам і зупиниться, якщо щось не так.

### Етап 2. Чи встановлено M.I.B.

Цей пакет **не встановлює M.I.B.** Як це зробити — описано в
[репозиторії M.I.B.](https://github.com/Mr-MIBonk/M.I.B._More-Incredible-Bash).

Ознака, що все готово: коли карту M.I.B. вставлено в SD1, у GEM є пункт **`=>M.I.B.<=`**
(`m.i.b.`). Без карти цього пункту немає. Якщо після холодного запуску блока GEM
не відкривається чи пункту немає — зачекайте **до 5 хвилин** і перевірте ще раз.

**Як відкрити GEM.** Робіть це на **головному екрані (Home)**. GEM з'являється **лише після**
встановлення M.I.B. (воно вмикає Development Mode); червоне меню (REM) доступне завжди.
Комбінація — на пультах біля шахти ручки, де є дві червоні клавіші-«качелі»: ліва
**NAV/MAP** і права **RADIO/MEDIA**. Стрілки на картинках у
[таблиці M.I.B.](https://github.com/Mr-MIBonk/M.I.B._More-Incredible-Bash/wiki/%22hidden-menus%22---key-combinations)
показують, **яку частину** клавіші натиснути (↑ — верхню, ↓ — нижню).

| Модель | GEM (зелене меню) | Перезавантаження (жорстке) |
| --- | --- | --- |
| A4 / A5 / Q5 2017–2020 | Одночасно утримуйте **верх NAV/MAP** і **верх RADIO** | Ті самі дві клавіші **плюс натиснута ручка** |
| A4 (8W) з механічною КПП | Те саме: **верх NAV/MAP** + **верх RADIO** (пульт інший, розташування клавіш відрізняється — дивіться картинку) | Ті самі дві клавіші + натиснута ручка |
| Q7 2014–2020 | Одночасно **верх NAV/MAP** і **верх RADIO/MEDIA** (клавіші внизу панелі) | Ті самі дві клавіші + натиснута ручка |

Утримуйте кілька секунд, поки не з'явиться меню. M.I.B. не вказує точного часу для Audi
(для Porsche — близько 5 с). Якщо не вийшло — переконайтеся, що ви на Home і що минуло
до 5 хвилин після холодного старту. Червоне меню (REM) — **нижня** частина правої клавіші
замість верхньої; його не плутайте з GEM.

### Етап 3. Підготовка SD-карти (на комп'ютері)

1. **Завантажте реліз**, а не вихідний код. На сторінці
   [Releases](https://github.com/yety-ua/mhi2-ukrainian-localization/releases) візьміть
   `mhi2-ukrainian-localization-k3346-v1.0.0-preview.6.zip` і поруч файл `.sha256`.
   Кнопка «Source code (zip)» — **не те**: це вихідники, а не готова карта.
2. **Перевірте, що файл не пошкоджений.** Порівняйте суму з вмістом `.sha256`.

   Windows (PowerShell, у теці із завантаженням):

   ```powershell
   Get-FileHash .\mhi2-ukrainian-localization-k3346-v1.0.0-preview.6.zip -Algorithm SHA256
   Get-Content .\mhi2-ukrainian-localization-k3346-v1.0.0-preview.6.zip.sha256
   ```

   macOS / Linux:

   ```sh
   shasum -a 256 -c mhi2-ukrainian-localization-k3346-v1.0.0-preview.6.zip.sha256
   ```

   Рядки хешу мають збігатися (у macOS — `OK`). Не збігаються — завантажте знову.
3. **Збережіть M.I.B.-карту.** Скопіюйте весь вміст вашої робочої SD-карти на комп'ютер як
   запасну копію. Якщо на карті вже є `mod/custom.sh` чи `mod/command.sh`, збережіть їх під іншими назвами:
   наш файл його замінює і **не запускає** старі команди.
4. **Розпакуйте архів** і скопіюйте:
   - теку **`uk-localization`** — у **корінь** карти (поруч з `apps`, `config`, `mod`…);
   - файли **`mod/custom.sh`** і **`mod/command.sh`** — у вже наявну теку `mod` на карті (з заміною).

   Не створюйте проміжної теки з назвою архіву. Найчастіша помилка — вкладеність
   `SD/mhi2-ukrainian-…/uk-localization/…`.
5. **Звірте з картинкою.** На карті мають бути `apps/`, `config/`, `esd/`, `Launcher/`,
   `mod/custom.sh`, `mod/command.sh` і `uk-localization/` із файлами `ACTION.txt`, `HMI.sha1`, `SHA1SUMS`,
   `package.json` та теками `scripts/`, `payload/`, `stock/`, `target/`.
   Дерево — у [README](../README.md#підготовка-sd-карти).
6. **Безпечно вилучіть карту** з комп'ютера (щоб файли дописалися). На macOS після копіювання
   можуть з'явитися службові файли `._*` — вони не заважають.
7. **Оновлення з preview.1:** спершу виконайте його `RESTORE`, потім ставте цей реліз. З preview.2/3 достатньо замінити `uk-localization/` і `mod/` (**у preview.2/3 не було `mod/command.sh`**, тому на M.I.B. V3.6+ пункт нічого не запускав).

### Етап 4. Перша перевірка — `CHECK` (нічого не змінює)

1. Вставте карту в **SD1**. Нічого редагувати не треба: в `ACTION.txt` уже стоїть `CHECK`.
2. У GEM: **`m.i.b.` → `Advanced Settings` → `Run individual script`** (так у M.I.B. V3.6+; на екрані
   підказка «Place command.sh with script in /mod/ folder»). У старіших версіях пункт називається
   `Run Custom Script` / `Run /mod/custom.sh from m.i.b. SD`. Запустіть.
3. Очікуваний результат: рядок **`CHECK PASS`** і код **`0`**. Якщо екран прокрутився
   надто швидко — відкрийте лог на карті на комп'ютері: `uk-localization/logs/run-….log`.
4. Напис M.I.B. «execution finished» (у V3.7.1 — «it is all done!») **нічого не означає** — він з'являється навіть при
   помилці. Дивіться тільки на `CHECK PASS` / `SUCCESS` / `ERROR` і код.

5. Після `CHECK PASS` ви побачите підказку на кшталт `Nothing was changed. To INSTALL, run
   this same GEM item again (step 1 of 3 done)`. Це **не помилка**, а перший із трьох кроків:
   встановлення почнеться лише після ще двох запусків поспіль. Не хочете встановлювати —
   просто не запускайте пункт знову.

> **Увага:** три запуски цього пункту підряд = встановлення. Якщо хочете лише перевіряти,
> не запускайте його втретє; перезапуск MMI скасовує будь-який незавершений крок.

Що робити, якщо не `PASS` — у [таблиці проблем](#якщо-щось-пішло-не-так).

### Етап 5. Страховка перед встановленням

Пройдіть **усе** перед `INSTALL`. Пакет вимагає ці кроки не для галочки: без них
невдалий запис може лишити блок без меню, а ви не матимете способу це виправити.

**5.1 Живлення.** Забезпечте стабільне живлення авто на весь час (див. «Що потрібно»).

**5.2 Запасний вхід по telnet (готуйте заздалегідь, перевіряйте в авто).**
Це мережевий вхід у блок із ноутбука, коли екран MMI не працює. Що важливо знати про нього
(перевірено на реальному A4 під час розробки):

- **Telnet (порт 23) працює лише через USB-Ethernet адаптер** у USB блока. Через Wi-Fi
  точку доступу MMI брандмауер блока пропускає тільки порт 22 (SSH), а порт 23 — ні.
- **Не кожен адаптер підійде.** M.I.B. офіційно підтримує D-Link DUB-E100 (rev. D1); інші чипи
  ASIX додає пункт `Advanced Settings → add_usb_ethernet_devices → Install devices (again)`
  (AX88179, AX88772/A/B/C). **Увага:** цей пункт назавжди записує файл у блок і сам
  перезавантажує його через ~10 с, тож робіть його свідомо й не під час іншої операції.
  На авто розробника адаптер на AX88179 (`0b95:1790`) визначився й отримував кадри, але
  нічого не передавав (ping/22/23 не відповідали); радили AX88772A/B або DUB-E100.
- **Логін і пароль.** M.I.B. **не вмикає** telnet (це штатна служба блока) і **не задає** пароль.
  Логін — `root`, а пароль залежить від версії ПЗ (SW train) вашого блока. Готовий список
  лежить у корені M.I.B. на вашій карті: файл **`Password_List_V4.0.pdf`**. Знайдіть там рядок
  для своєї версії ПЗ заздалегідь. У гайді пароль не наводиться.

<details>
<summary>Детальні кроки: як перевірити telnet (натисніть, щоб розгорнути)</summary>

1. Вдома ввімкніть клієнт telnet у Windows: PowerShell **від адміністратора**:

   ```powershell
   dism /online /Enable-Feature /FeatureName:TelnetClient /All
   ```

   Або встановіть [PuTTY](https://www.putty.org/) (тип з'єднання **Telnet**, порт **23**).
2. У авто під'єднайте USB-Ethernet адаптер до USB блока, кабель — до ноутбука. Зачекайте
   15–20 секунд, поки Windows побачить мережу. Адреса блока в M.I.B. — `172.16.250.248`
   (її можна підтвердити в GEM: `Network_configuration → ethernet_configuration → Show IP-Address`).
3. Перевірте порт:

   ```powershell
   Test-NetConnection 172.16.250.248 -Port 23
   ```

   Має бути `TcpTestSucceeded : True`.
4. Перевірте **справжній вхід**, а не лише відкритий порт: `telnet 172.16.250.248`, логін `root`,
   пароль зі списку M.I.B. Виконайте `ls /mnt/app`, потім `exit`.

Якщо адаптер «горить», але порт не відкривається або пінг відповідає тільки на дуже малі
пакети — найімовірніше, це несумісний чип адаптера: спробуйте інший (див. вище).

</details>

Не вдалося — **не робіть `INSTALL`**. Лишайтеся на `CHECK`.

> **SSH по Wi-Fi замість telnet.** У M.I.B. є `Advanced Settings → install_sshd` (SSH, порт 22).
> Після нього блок приймає вхід `root` на порту 22 і через Wi-Fi точку доступу MMI, пароль той
> самий, що в списку M.I.B. (або ключ, якщо покласти `Custom/id_rsa.pub` на SD). У авто
> розробника саме цей шлях працював, коли USB-Ethernet не заробив; та сама команда
> відновлення виконується і в такому SSH-сеансі. Мінуси: `install_sshd` **змінює блок**
> (inetd, правила мережі, `.profile`) і відкриває порт 22 на Wi-Fi — не тримайте точку
> доступу ввімкненою без потреби. Пакет формально розрахований на telnet; SSH — запасний
> варіант, а не гарантія. Обидва способи працюють лише тоді, коли ОС блока ще завантажується.

**5.3 Повний бекап M.I.B.** У GEM: `m.i.b.` → `backup_restore` → **Standard Backup**
(назви можуть відрізнятися залежно від версії M.I.B.). Дочекайтеся завершення, не вибирайте
Patch / Restore / SW Update. Потім скопіюйте створену теку `backup` із карти на комп'ютер і
перегляньте лог на помилки. Повідомлення «завершено» саме по собі повноти копії не доводить.

**5.4 Місце.** Інсталятор вимагає ≥ 40 000 KiB вільного в `/mnt/app` і сам це перевірить у
`CHECK`.

### Етап 6. Встановлення — `INSTALL`

Ноутбук і редагування файлів не потрібні: дію вибирає **повторний запуск** того самого пункту GEM
(`m.i.b. → Advanced Settings → Run individual script`). Крок 1 із 3 ви вже зробили на Етапі 4.

1. Переконайтеся, що пройшли весь Етап 5 (живлення, запасний вхід, бекап).
2. Запустіть пункт **вдруге**. З'явиться `CONFIRM (step 2 of 3)` і три умови (живлення,
   перевірений запасний вхід, повний бекап). Нічого не змінюється. Якщо хоч одна умова не
   виконана — зупиніться й перезапустіть MMI: крок скасується.
3. Запустіть пункт **втретє**: `Step 3 of 3 confirmed: running INSTALL now.` — почнеться
   встановлення.
4. **Поки йде робота:** не виймайте карту, не натискайте Back, не запускайте інші операції
   M.I.B. (бекап, перезавантаження, прошивку), не вимикайте запалювання.
5. Скрипт збереже оригінали (в блоці й на карті), встановить файли, запише параметр `2D00`
   останнім і перевірить запис.
6. Очікуваний результат: **`SUCCESS: INSTALL`** і код **`0`**. Тільки тоді переходьте до
   Етапу 7. Автоматичного перезавантаження **немає**.

Якщо між запусками MMI перезапускали або була помилка — відлік починається спочатку.

<details>
<summary>Запасний шлях: вибрати дію через файл ACTION.txt (потрібен комп'ютер)</summary>

Слово в `ACTION.txt`, відмінне від `CHECK`, виконується **одразу, за один запуск**. Знадобиться,
наприклад, для `VOICE_INSTALL`.

1. Вийміть карту з блока й на комп'ютері замініть вміст `uk-localization/ACTION.txt` на одне слово
   (`INSTALL`, `RESTORE`…).

   > **Пастка:** скрипт приймає **лише** слово з переносом рядка LF. Звичайний Блокнот
   > Windows зберігає з переносом CRLF — тоді скрипт відповість `Invalid action`. Використайте
   > команду нижче (диск `E:` замініть на свій):

   Windows (PowerShell):

   ```powershell
   [IO.File]::WriteAllText("E:\uk-localization\ACTION.txt", "INSTALL`n")
   [IO.File]::ReadAllBytes("E:\uk-localization\ACTION.txt").Length
   ```

   Друга команда має вивести **8** для `INSTALL` (9 — зайвий символ CRLF; запишіть ще раз).

   macOS / Linux:

   ```sh
   printf 'INSTALL\n' > /Volumes/SDCARD/uk-localization/ACTION.txt
   ```

   Якщо редагуєте в редакторі, кодування — UTF-8 **без BOM**.
2. Безпечно вилучіть карту, вставте в **SD1**, запустіть пункт GEM один раз. Після дії
   скрипт сам повертає `ACTION.txt` до `CHECK`.

</details>

**Якщо встановлення перервалося (лог містить `Interrupted operation recorded` або стан
`PENDING`) — не перезавантажуйте блок. Одразу переходьте до розділу «Якщо щось пішло не так».**

### Етап 7. Перезавантаження й перевірка

1. Перезапустіть MMI вручну: вимкніть запалювання й дочекайтеся повного вимкнення блока
   (кілька хвилин), потім увімкніть. Якщо блок «завис» — жорстке перезавантаження комбінацією
   з таблиці в Етапі 2 (дві клавіші + ручка). M.I.B. застерігає, що жорсткий ребут
   може втратити частину незбережених змін кодування; тому це запасний варіант.
2. Налаштування → Мова → оберіть **«Українська»**.
3. Перевірте: головне меню; введення тексту (смуга з 33 літерами — це ручка/тачпад, не QWERTY);
   телефон; налаштування; діагностика — чи немає помилок у блоці.
4. **Холодний старт без карти:** вийміть SD, вимкніть авто на кілька хвилин, увімкніть.
   Українська має лишитися. На авто це ще **не доведено** — ваш результат цінний.

### Якщо щось пішло не так

<details>
<summary>Таблиця помилок і що робити (натисніть, щоб розгорнути)</summary>

| Що бачите | Що це означає | Що робити |
| --- | --- | --- |
| Немає пункту `m.i.b.` в GEM | Немає карти в SD1 або блок ще не завантажився | Перевірте слот, зачекайте до 5 хв |
| `Nothing to do!` після «Run individual script» | У `mod/` на карті немає `command.sh` (M.I.B. V3.6+ шукає саме його) | Скопіюйте `mod/command.sh` із релізу preview.4 або новішого поруч із `custom.sh` |
| `syntax error` / `unexpected` у `localization.sh` | Помилка розбору скрипта оболонкою блока; лог `run-*.log` у такому разі не створюється | Надішліть фото екрана і файл `uk-localization/logs/launcher-errors.txt` (з preview.5 він зберігається на карті) |
| `ERROR: uk-localization package is missing from SD1` | Теку скопійовано не в корінь | Виправте вкладеність (Етап 3, п. 4) |
| `step 1 of 3 done` / `step 2 of 3` | Це підказка, не помилка | Нічого не робіть, якщо не хочете йти далі |
| `Invalid action…` | Лише якщо ви вручну редагували `ACTION.txt`: зайвий CR/пробіл/BOM | Перезапишіть командою із запасного шляху Етапу 6 |
| `HMI is not the exact reviewed K3346/MU1438 binary` або схожі «not stock» | Версія/файли не ті, або вже щось змінено | **Нічого не змушуйте.** Не підтримується. Надішліть лог |
| `At least 40000 KiB free…` | Мало місця в блоці | Надішліть лог; не видаляйте нічого самі |
| `Another localization operation or stale lock exists` | Попередній запуск перервався | Не видаляйте `/tmp/uk-localization.lock`, поки не впевнені, що нічого не виконується |
| `M.I.B. backup/reboot/flash is running` | Йде інша операція M.I.B. | Дочекайтеся її завершення |
| `Interrupted operation recorded; run RESTORE…` / `PENDING` | Встановлення перервано | **Не перезавантажуйте.** Виконайте `RESTORE` (нижче) |
| Блок не запускає меню | HMI/GEM не стартує | Відновлення по telnet (нижче) |

</details>

**Відновити оригінал (меню працює).** Запустіть пункт GEM **тричі підряд**: у стані «встановлено»
перший запуск пише `Ukrainian is installed and verified; nothing needs to be done` і пропонує
відновлення (`step 1 of 3`), другий показує чеклист, третій виконує `RESTORE`. Те саме, якщо
встановлення перервалося (`PENDING`) або файли розійшлися з пакетом: тоді перший запуск
завершується повідомленням про проблему та пропозицією відновлення. Дочекайтеся
**`SUCCESS: RESTORE`** і коду `0`. Бекапи й логи лишаються. Запасний шлях: слово `RESTORE`
в `ACTION.txt` виконується за один запуск.

**Відновити оригінал (меню не працює).** Підключіть ноутбук, як на 5.2, зайдіть telnet і
виконайте:

```sh
/bin/sh /mnt/app/root/uk-localization/recovery/scripts/localization.sh RESTORE
```

Дочекайтеся `SUCCESS: RESTORE` і коду `0`, **і лише тоді** перезавантажуйте. Не
використовуйте `force`. Якщо магнітола взагалі не завантажує QNX — це вже поза межами
пакета: використовуйте повний бекап M.I.B. з Етапу 5.

### Що надіслати, якщо потрібна допомога

<details>
<summary>Що надіслати, якщо потрібна допомога</summary>

Відкрийте [issue](https://github.com/yety-ua/mhi2-ukrainian-localization/issues) і додайте:
вміст `uk-localization/logs/run-*.log`, на якому етапі зупинилися, модель авто й версію MMI.
**Не публікуйте** VIN, пароли й особисті дані з логів.

</details>

### Необов'язкове: англійський голос

<details>
<summary>Англійський голос (необов'язково, для першого встановлення пропустіть)</summary>

`VOICE_INSTALL` — окремий компонент, **не українські голос і розпізнавання**. Для першого
встановлення його **пропустіть**. Спершу переконайтеся, що український інтерфейс працює.

</details>

---

## English

This guide is for people installing **for the first time** who do not know M.I.B. The
[README](../README.md) stays the short reference; this explains each step, what you should
see and what to do when you see something else.

### Honest status first

- The package is **preview**. It has been tested on a computer and in an emulator, but
  **not yet on a real car**. You are among the first. A failed write can leave a head
  unit that does not boot.
- It does **not** flash firmware: it replaces language files and one parameter. Everything
  it touches is copied first, and `RESTORE` puts the originals back.
- **If you are unsure, or you have no fallback access (Stage 5), stop at Stage 4
  (`CHECK`).** It changes nothing and already tells you whether the package fits.

### Glossary

<details>
<summary>Show glossary (GEM, SD1, MMX…)</summary>

| Term | Meaning |
| --- | --- |
| **Head unit / MMI** | The unit with the screen in the car. |
| **M.I.B.** | Free script toolkit on an SD card, started from the unit's hidden menu. This package runs **through** it. |
| **GEM** | Green Engineering Menu, the hidden service menu. Shows an `m.i.b.` entry when M.I.B. is installed and its SD card is inserted. |
| **SD1** | The first SD slot. The M.I.B. card must be in it. |
| **ACTION.txt** | One file with one word on the card: `CHECK`, `INSTALL`, `RESTORE`. |
| **CHECK** | Look-only mode; installs nothing. |
| **telnet / port 23** | Fallback network login to the unit from a laptop; only needed if the menu stops working. |
| **Log** | `uk-localization/logs/run-….log` on the card. |

</details>

### Overview

| Stage | What you do | Changes the car? |
| --- | --- | --- |
| 1 | Check the package fits | no |
| 2 | Confirm M.I.B. already works | no |
| 3 | Prepare the SD card | no |
| 4 | Run the GEM item: `CHECK` (step 1 of 3) | **no** |
| 5 | Safety net: fallback access, backup, power | creates copies |
| 6 | Run the same item **two more times** (checklist, then `INSTALL`) | **yes** |
| 7 | Reboot and verify | — |

### What you need

- A **FAT32** SD card already used with M.I.B. (32 GB or smaller is recommended; the
  write-protect switch must be unlocked) and a card reader.
- A car with **MMI K3346 / MU1438** and **M.I.B. already installed**.
- For Stage 5: a Windows laptop, a USB-Ethernet adapter the unit recognises plus a cable,
  and external vehicle power support. Running the engine is **not** a substitute.
- Do not rush. During writing: do not remove the card, press Back or switch ignition off.

### Stage 1. Does it fit?

Only `MHI2_ER_AUG22_K3346`, MU `1438`, HMI `HMI_AU_MIB2_H_EU_G22_C6_190300`. The
installer **rejects anything else on its own**. Covered models (this firmware): **A4, A5, Q5, Q7**.
**Not supported:** any A3, TT, R8, A6/A7 and other MMIs, even if their GEM combinations look similar. You can look at the version in the MMI
settings beforehand (menu names vary), or simply run `CHECK`.

### Stage 2. Is M.I.B. installed?

This package does not install M.I.B.; see the
[M.I.B. repository](https://github.com/Mr-MIBonk/M.I.B._More-Incredible-Bash). When it is
ready, GEM shows **`=>M.I.B.<=`** with the card in SD1. After a cold start GEM can take
**up to 5 minutes** to become available. **How to open GEM.** Do it on the **Home screen**. GEM exists **only after** M.I.B. is installed
(it enables Development Mode); the red menu (REM) is always available. The combination uses the two
red rocker keys next to the knob: left **NAV/MAP** and right **RADIO/MEDIA**. The arrows in the
[M.I.B. table](https://github.com/Mr-MIBonk/M.I.B._More-Incredible-Bash/wiki/%22hidden-menus%22---key-combinations)
show **which half** of a key to press (↑ upper, ↓ lower).

| Model | GEM (green menu) | Reboot (hard) |
| --- | --- | --- |
| A4 / A5 / Q5 2017–2020 | Hold **upper NAV/MAP** and **upper RADIO** together | Same two keys **plus pressing the knob** |
| A4 (8W) manual gearbox | Same: **upper NAV/MAP** + **upper RADIO** (different panel; key positions differ, see the picture) | Same two keys + knob press |
| Q7 2014–2020 | **Upper NAV/MAP** and **upper RADIO/MEDIA** together (keys at the bottom of the panel) | Same two keys + knob press |

Hold for a few seconds until the menu appears; M.I.B. gives no exact time for Audi (about 5 s
for Porsche). If it fails, make sure you are on Home and that up to 5 minutes passed since
a cold start. REM uses the **lower** half of the right key instead; do not confuse it with GEM.

### Stage 3. Prepare the SD card

1. Download the **release** ZIP and its `.sha256` from
   [Releases](https://github.com/yety-ua/mhi2-ukrainian-localization/releases), not "Source code".
2. Verify the checksum.

   Windows:

   ```powershell
   Get-FileHash .\mhi2-ukrainian-localization-k3346-v1.0.0-preview.6.zip -Algorithm SHA256
   Get-Content .\mhi2-ukrainian-localization-k3346-v1.0.0-preview.6.zip.sha256
   ```

   macOS / Linux:

   ```sh
   shasum -a 256 -c mhi2-ukrainian-localization-k3346-v1.0.0-preview.6.zip.sha256
   ```

3. Copy your whole working M.I.B. card to the computer as a spare. If `mod/custom.sh` or `mod/command.sh`
   exists, rename copies first: ours replaces it and does not chain old commands.
4. Extract the release. Copy the **`uk-localization`** folder to the **card root** (next
   to `apps`, `config`, `mod`) and **`mod/custom.sh`** and **`mod/command.sh`** into the existing `mod` folder.
   No extra wrapper folder — the most common mistake.
5. Compare with the tree in the [README](../README.md#prepare-the-sd-card), then eject safely.
6. Upgrading from preview.1: run its `RESTORE` first. From preview.2/3 replace `uk-localization/` and `mod/` (**preview.2/3 lacked `mod/command.sh`**, so on M.I.B. V3.6+ the item ran nothing).

### Stage 4. First check — `CHECK`

1. Put the card in **SD1**. Nothing to edit: `ACTION.txt` already says `CHECK`.
2. GEM → **`m.i.b.` → `Advanced Settings` → `Run individual script`** (M.I.B. V3.6+; the screen hints
   “Place command.sh with script in /mod/ folder”). Older versions: `Run Custom Script` /
   `Run /mod/custom.sh from m.i.b. SD`.
3. Expect **`CHECK PASS`** and exit code **`0`**. If the output scrolled away, read
   `uk-localization/logs/run-….log` on the card.
4. The M.I.B. message “execution finished” (V3.7.1: “it is all done!”) means nothing; rely on `CHECK PASS` /
   `SUCCESS` / `ERROR` and the code. See the [troubleshooting table](#if-something-goes-wrong).
5. After `CHECK PASS` you will see a hint like `Nothing was changed. To INSTALL, run this same
   GEM item again (step 1 of 3 done)`. This is **not an error**; it is the first of three steps:
   installation starts only after two more runs in a row. If you do not want to install,
   simply do not run the item again.

> **Note:** three runs of this item in a row = installation. To only verify, do not run it a
> third time; restarting the MMI cancels any unfinished step.

### Stage 5. Safety net before installing

Do **all** of it before `INSTALL`.

- **Power:** stable vehicle power for the whole operation.
- **Fallback telnet access** (prepare beforehand, verify in the car). Facts verified on a real A4
  during development:
  - **Telnet (port 23) works only through a USB-Ethernet adapter** in the unit's USB. Over the MMI
    Wi-Fi hotspot the unit's firewall passes only port 22 (SSH), not 23.
  - **Not every adapter works.** M.I.B. officially supports the D-Link DUB-E100 (rev. D1); other ASIX
    chips are added by `Advanced Settings → add_usb_ethernet_devices → Install devices (again)`
    (AX88179, AX88772/A/B/C). **Note:** that item writes a file into the unit permanently and
    reboots it after ~10 s, so run it deliberately. On the developer's car an AX88179 (`0b95:1790`)
    adapter enumerated and received frames but transmitted nothing (ping/22/23 failed); an
    AX88772A/B or DUB-E100 is the recommended choice.
  - **Login and password.** M.I.B. does **not** enable telnet (stock service) and does **not** set a
    password. Login is `root`; the password depends on your unit's software (SW train). The list
    ships in the M.I.B. root on your card: **`Password_List_V4.0.pdf`**. Look up your version in
    advance. This guide does not quote passwords.
  - Steps: (1) enable the Windows telnet client (admin PowerShell:
    `dism /online /Enable-Feature /FeatureName:TelnetClient /All`) or use PuTTY (Telnet, port 23);
    (2) in the car connect the adapter to the unit and a cable to the laptop, wait 15–20 s; the unit
    address is `172.16.250.248` (confirm in GEM: `Network_configuration → ethernet_configuration →
    Show IP-Address`); (3) `Test-NetConnection 172.16.250.248 -Port 23` must show
    `TcpTestSucceeded : True`; (4) verify a **real login**: `telnet 172.16.250.248`, `root` + the
    password from the list, run `ls /mnt/app`, `exit`.
  - If the link is up but the port does not open (or ping only answers tiny packets), suspect an
    incompatible adapter chip; try another.
  If this fails, **do not run `INSTALL`**.

  > **SSH over Wi-Fi instead of telnet.** After `Advanced Settings → install_sshd` the unit accepts
  > `root` on port 22 also through the MMI hotspot, with the same password from the list (or a key
  > via `Custom/id_rsa.pub`). On the developer's car this worked when USB-Ethernet did not, and the
  > same recovery command runs in such an SSH session. Downsides: `install_sshd` **modifies the
  > unit** (inetd, network rules, `.profile`) and opens port 22 on Wi-Fi, so do not leave the hotspot
  > on needlessly. The package is formally designed around telnet; SSH is a fallback, not a
  > guarantee. Both work only while the unit's OS still boots.
- **Full M.I.B. backup:** GEM → `m.i.b.` → `backup_restore` → **Standard Backup** (names may
  vary by M.I.B. version). Never pick Patch / Restore / SW Update. Copy the resulting
  `backup` folder to the computer and read its log for errors.
- **Free space:** ≥ 40,000 KiB in `/mnt/app`; `CHECK` verifies it.

### Stage 6. Install — `INSTALL`

No laptop and no file editing: the action is chosen by **running the same GEM item again**
(`m.i.b. → Advanced Settings → Run individual script`). You already did step 1 of 3 in Stage 4.

1. Make sure all of Stage 5 is done (power, fallback access, backup).
2. Run the item a **second time**. It shows `CONFIRM (step 2 of 3)` and three conditions (power,
   verified fallback access, full backup). Nothing changes. If any condition is not met, stop and
   restart the MMI: the step is cancelled.
3. Run it a **third time**: `Step 3 of 3 confirmed: running INSTALL now.` — installation starts.
4. While it runs: do not remove the card, press Back, run other M.I.B. operations or switch
   ignition off.
5. Expect **`SUCCESS: INSTALL`** and exit code **`0`**. There is **no automatic reboot**.
6. **If the install was interrupted (`PENDING` state / `Interrupted operation recorded`), do not
   reboot.** Go to the troubleshooting section and run `RESTORE`.

If the MMI was restarted between runs, or an error occurred, counting starts over.

<details>
<summary>Fallback: choose the action through ACTION.txt (needs a computer)</summary>

A word other than `CHECK` in `ACTION.txt` runs **at once, in a single launch** (needed e.g. for
`VOICE_INSTALL`).

1. Remove the card and on the computer set the single word in `uk-localization/ACTION.txt`
   (`INSTALL`, `RESTORE`…).

   > **Trap:** the script accepts the word with an **LF** line ending only. Windows Notepad
   > usually saves **CRLF**, which gives `Invalid action`. Use (replace `E:`):

   ```powershell
   [IO.File]::WriteAllText("E:\uk-localization\ACTION.txt", "INSTALL`n")
   [IO.File]::ReadAllBytes("E:\uk-localization\ACTION.txt").Length
   ```

   The second command must print **8** for `INSTALL` (9 means CRLF). macOS / Linux:
   `printf 'INSTALL\n' > /Volumes/SDCARD/uk-localization/ACTION.txt`. In an editor use
   UTF-8 **without BOM**.
2. Eject safely, insert in **SD1**, run the GEM item once. Afterwards the script resets
   `ACTION.txt` to `CHECK` itself.

</details>

### Stage 7. Reboot and verify

1. Reboot the MMI manually: ignition off, wait until the unit is fully off (a few minutes),
   then on. If it hangs, use the hard-reboot combination from Stage 2 (two keys + knob press);
   M.I.B. warns that a hard reboot can lose some unsaved coding changes, so it is a fallback.
2. Settings → Language → **“Українська”**.
3. Check the main menu, text entry (the 33-letter band is for the knob/touchpad, not QWERTY),
   phone, settings and diagnostics.
4. **Cold boot without the card:** remove the SD, switch the car off for a few minutes,
   start again. Ukrainian should persist. This is **not yet proven** on a car, so your result matters.

### If something goes wrong

<details>
<summary>Troubleshooting table (click to expand)</summary>

| Symptom | Meaning | Action |
| --- | --- | --- |
| No `m.i.b.` entry in GEM | No card in SD1 or the unit is still starting | Check the slot, wait up to 5 min |
| `Nothing to do!` after “Run individual script” | `mod/command.sh` is missing on the card (M.I.B. V3.6+ looks for it) | Copy `mod/command.sh` from release preview.4 or newer next to `custom.sh` |
| `syntax error` / `unexpected` in `localization.sh` | The unit's shell failed to parse the script; no `run-*.log` is created in that case | Send a photo of the screen and `uk-localization/logs/launcher-errors.txt` (kept on the card since preview.5) |
| `uk-localization package is missing from SD1` | Folder not in the card root | Fix nesting (Stage 3, step 4) |
| `step 1 of 3 done` / `step 2 of 3` | A hint, not an error | Do nothing unless you want to continue |
| `Invalid action…` | Only if you edited `ACTION.txt` by hand: stray CR / space / BOM | Rewrite with the Stage 6 fallback command |
| `HMI is not the exact reviewed K3346/MU1438 binary`, “not stock” | Wrong version, or already modified | Do not force; unsupported. Send the log |
| `At least 40000 KiB free…` | Not enough space | Send the log; delete nothing yourself |
| `Another localization operation or stale lock exists` | Previous run was interrupted | Do not delete `/tmp/uk-localization.lock` until you are sure nothing is running |
| `M.I.B. backup/reboot/flash is running` | Another M.I.B. operation | Wait for it |
| `Interrupted operation recorded` / `PENDING` | Install interrupted | **Do not reboot.** Run `RESTORE` |
| Unit does not show the menu | HMI/GEM will not start | Recover over telnet (below) |

</details>

**Restore (menu works):** run the GEM item **three times in a row**: in the installed state the
first run prints `Ukrainian is installed and verified; nothing needs to be done` and offers
restoration (`step 1 of 3`), the second shows the checklist, the third performs `RESTORE`.
The same happens after an interrupted install (`PENDING`) or when files drifted from the
package: the first run ends with the problem message and the restore offer. Wait for
**`SUCCESS: RESTORE`** and code `0`. Backups and logs stay. Fallback: the word `RESTORE` in
`ACTION.txt` runs in a single launch.

**Restore (menu does not work):** connect the laptop as in Stage 5, telnet in and run:

```sh
/bin/sh /mnt/app/root/uk-localization/recovery/scripts/localization.sh RESTORE
```

Reboot only after `SUCCESS: RESTORE` and code `0`. Never use `force`. If the unit cannot
boot QNX at all, that is beyond this package; use the full M.I.B. backup from Stage 5.

### Asking for help

<details>
<summary>What to send when asking for help</summary>

Open an [issue](https://github.com/yety-ua/mhi2-ukrainian-localization/issues) with the contents of
`uk-localization/logs/run-*.log`, the stage you stopped at, the car model and MMI version.
Do **not** post VINs, passwords or personal data found in logs.

</details>

### Optional: English voice

<details>
<summary>English voice (optional, skip on the first install)</summary>

`VOICE_INSTALL` is a separate component, **not Ukrainian speech**. Skip it on the first
install and make sure the Ukrainian UI works first.

</details>
