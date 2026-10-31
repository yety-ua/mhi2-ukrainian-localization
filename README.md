# 🇺🇦 Ukrainian localization for Audi MHI2 — A4 / A5 / Q5 / Q7

**MHI2_ER_AUG22_K3346 · MU1438 · G22 · EvoHigh**

[Українська](#українська) · [English](#english) · [Покрокова інструкція / Step-by-step guide](docs/INSTALL_GUIDE.md) · [Download / Завантажити](https://github.com/yety-ua/mhi2-ukrainian-localization/releases) · [Глибина / Coverage](docs/LOCALIZATION_DEPTH.md) · [A4 provenance](docs/A4_PROVENANCE.md)

![Українське головне меню Audi A4 K3346 / Ukrainian Audi A4 K3346 main menu](docs/images/main-menu.png)

## Українська

Локалізація для штатної прошивки **Audi MHI2 K3346 на A4, A5, Q5 та Q7**: українські тексти,
вибір мови з прапорцем, українська смуга клавіатури та встановлення з однієї
SD-карти через [M.I.B.](https://github.com/Mr-MIBonk/M.I.B._More-Incredible-Bash).
Пакет додає ресурси й параметризацію; повна прошивка не перепрошивається.

**Статус: перевірено на одному авто** (A4 B9, K3346 / MU1438): встановлення,
`RESTORE` і повторне встановлення з SD-карти пройшли, українська працює в меню MMI.
Інші автомобілі й версії прошивки не перевірялися.
Це не твердження про 100% перекладу кожного доступного екрана. Повний опис
реалізованих частин і залишкових питань — у [документі глибини](docs/LOCALIZATION_DEPTH.md).

### Безкоштовне поширення та встановлення

Автор поширює цей мод **абсолютно безкоштовно для всіх охочих**. Завантаження,
використання та встановлення локалізації мають бути безкоштовними. Можна
встановити її самостійно або безкоштовно допомогти іншому власнику автомобіля.

**Продаж, перепродаж і заробіток на цьому моді заборонені.** Не дозволяється
брати плату за пакет, доступ до нього, його встановлення чи активацію, а також
включати його до платних пакетів, послуг або комерційних пропозицій.
При безкоштовному поширенні зберігайте ці умови, авторство та посилання на
[оригінальний репозиторій](https://github.com/yety-ua/mhi2-ukrainian-localization).

Ці умови стосуються авторського внеску цього проєкту. M.I.B. та ресурси сторонніх
правовласників зберігають власні ліцензії й умови; цей репозиторій не змінює їх.

### Що включено

- Українські таблиці **22 модулів**, збереження структури **15 400 штатних
  непорожніх слотів** і додаткова назва мови «Українська» — разом 15 401 слот.
- Вибір `uk_UA` у меню, український прапорець, конфігурація доступних мов і датасет `2D00`.
- **Клавіатура MMI:** смуга 33 українських літер `АБВГҐДЕЄЖЗИІЇЙКЛМНОПРСТУФХЦЧШЩЬЮЯ`,
  кирилиця за замовчуванням для української, без `Ё Ъ Ы Э`. Це смуга для ручки/тачпада, не QWERTY.
- Перевірка точної прошивки, контрольних сум, оригінальних ресурсів і CRC параметризації;
  резервні копії на SD та в голові; перевірка запису; окреме відновлення.
- Окремий необов'язковий компонент: **англійський** NAVI/TTS/SDS fallback.
  Українське голосове розпізнавання та український голос не додаються.

### Сумісність

| Параметр | Єдина ціль цього пакета |
| --- | --- |
| Моделі / платформа | Audi A4, A5, Q5, Q7 з наведеною нижче прошивкою / G22, MLB Evo |
| Firmware train | `MHI2_ER_AUG22_K3346` |
| MU | `1438` |
| HMI | `HMI_AU_MIB2_H_EU_G22_C6_190300`, `EvoHigh` |
| Носій | FAT32 SD-карта в **SD1** з повним M.I.B. (повнорозмірна, не microSD, від 4 ГБ, свіжо відформатована, без захисту від запису) |
| M.I.B. | V3.6+ (`Run individual script`); старіші версії запускають `Run Custom Script`. На авто пробувалась лише V3.7.1 MHIG (GEM 4.5s) |

Докладно, з доказами й перевіркою за пунктами: [яких авто стосується пакет](docs/COMPATIBILITY.md).
Інші MHI2, Audi A3 `AU37x/P5089`, MHI2Q, MIB3 та інші MU не підтримуються.
Інсталятор звіряє точний хеш образу HMI, а також train/MU (з файлів блока, запасно з EEPROM). A3 була
додатковим джерелом перекладів за збігом тексту, але структура, ID, класи й
параметризація цільового пакета належать A4 K3346. [Докази походження](docs/A4_PROVENANCE.md).

Вихідні ресурси та емуляторні докази перевірені на базі A4 B9. Перелік моделей
стосується цієї самої прошивки, а не всіх MMI на A4/A5/Q5/Q7. Для іншої моделі
інсталятор також вимагає збігу оригінальних ресурсів і датасетів; при розбіжності
він зупиниться. Окремих автомобільних випробувань цих моделей поки немає.

### Скріншоти

Власник зробив ці знімки **лише екрана MMI** в емуляторі K3346 13.10.2026.
Вони показують мову інтерфейсу, а не перевірку фізичного автомобіля.
Вони передують дев'ятьом правкам лише в Connectivity; показані модулі не змінені.

| Вибір української мови / Language selection | Телефон / Phone |
| --- | --- |
| ![Українська у списку мов](docs/images/language-menu.png) | ![Український екран підключення телефона](docs/images/phone.png) |

| Звук / Sound | Налаштування MMI / MMI settings |
| --- | --- |
| ![Українські налаштування звуку](docs/images/sound-settings.png) | ![Українські налаштування MMI](docs/images/mmi-settings.png) |

На окремих екранах емулятор неповністю відображає графічні віджети; це не
підтвердження такого самого дефекту на автомобілі. [Походження знімків](docs/screenshots.json).

### Швидке встановлення

1. Завантажте з [Releases](https://github.com/yety-ua/mhi2-ukrainian-localization/releases) файл `.zip`.
2. M.I.B. вже має стояти в голові (повний M.I.B. лежить на SD1). Розпакуйте архів і скопіюйте **вміст** його теки `mod/` у наявну `mod/` на SD-карті (саму теку `mod` не замінюйте).
3. Вставте карту в SD1 → GEM → `m.i.b.` → `Advanced Settings` → **`Run individual script`**.
4. **Читайте кінець виводу:** там статус і підказка, що робити далі. Повторюйте той самий пункт, доки не побачите `SUCCESS` (кожна дія: два запуски показують чеклист, третій виконує).
   - Нова голова: `CHECK PASS` → `INSTALL`.
   - Уже стоїть попередня версія пакета: `CHECK` запропонує `RESTORE` → потім `CHECK` → `INSTALL`.
5. Після `SUCCESS: INSTALL` повністю вимкніть запалювання (двері, замок, 3–5 хвилин) і ввімкніть. Виберіть «Українська» в Налаштування → MMI → Мова.

**Вперше з M.I.B.?** Є окрема [покрокова інструкція](docs/INSTALL_GUIDE.md#українська): словник, страховка (telnet, резервні копії), що робити, якщо щось пішло не так.
Перевірено: встановлення, `RESTORE` і повторне встановлення з SD-карти на одному авто (A4 B9, K3346 / MU1438, 2026-10-31). Інші авто й версії не перевірялися.

### Відновлення

Якщо щось пішло не так, або треба повернути оригінал: запустіть той самий пункт GEM (`Run individual script`); `CHECK` запропонує `RESTORE`, його виконує третій запуск поспіль. Запис, що перервався, інсталятор відкочує сам (`ROLLED BACK`). Детальні кроки, запасний шлях через telnet і довідка по `ACTION.txt` — у [докладному посібнику](docs/INSTALL_GUIDE.md#довідка-українська).

### Глибина, походження та обмеження

Читайте [огляд глибини](docs/LOCALIZATION_DEPTH.md), [перевірку A4/A3](docs/A4_PROVENANCE.md)
і [редакційні правки Connectivity](docs/connectivity-review-2026-10-13.json).
Клавіатура включена; рукописний рушій лишається `ru_RU`, а повне розпізнавання
українських штрихів не доведене. Навігаційні пошук/маршрути та Virtual Cockpit
перевіряються окремо. VC0313 не отримає українські ресурси з цього пакета.
Деякі команди, бренди, діагностичні/регіональні тексти залишаються англійською;
не всі редакційні кандидати означають відсутній переклад.

### Українська у Virtual Cockpit: що очікувати

**Українська в MMI не означає автоматично українську в кокпіті.** Панель приладів
має власні мовні ресурси. Цей SD-пакет їх не встановлює та VC не перепрошиває.

| Автомобілі / гілка VC | Версія VC | Попередній результат |
| --- | --- | --- |
| A4/A5/Q5, AU491 | **0313** | **Українську не підхопить:** штатна версія відхиляє код мови 43 |
| A4/A5/Q5, AU491 | **0379** | **Працює на авто:** код 43 і власні українські ресурси підтверджені; на A4 B9 (блок 8W5 920 790 D, H15, ПЗ 0379, оновлено з 0313) українська показується в кокпіті, 2026-10-31 |
| Q7, AU736 | **0310** | **Українську не підхопить:** перевірений бінарник відхиляє код мови 43 |
| Q7, AU736 | **0378** | **Мовна підтримка є:** код 43 і власні українські ресурси підтверджені бінарно |
| Q7, AU736 | **0416** | **Мовна підтримка є:** код 43 і власні українські ресурси підтверджені бінарно |

**H15 не є автоматичною забороною для 0379**, але результати роботи компаса після
оновлення суперечливі. Вища H-ревізія теж не є універсальною гарантією сумісності.
Не вибирайте прошивку лише за номером версії або назвою моделі.

[Повне дослідження VC: версії, H15/H17/H18/H19, компас, Q7/TPMS та джерела](docs/VC_COMPATIBILITY.md).
Для підбору потрібна ідентичність блока 17 (панель приладів): номери HW/SW,
H-ревізія, поточна версія ПЗ, модельний рік і регіон. Мовна підтримка у 0378/0416
не означає дозволу встановити ці версії на будь-яку Q7: показ на авто та сумісність
із конкретним залізом/комплектацією перевіряються окремо.

## English

A Ukrainian localization overlay for **Audi MHI2 K3346 on A4, A5, Q5 and Q7**,
installed from a single FAT32 SD1 card through M.I.B. It includes Ukrainian UI
tables, language selection, the Ukrainian alphabet band and reversible resource
installation with language parameterization. No full firmware/IFS update is performed.

**Status: verified on one car** (A4 B9, K3346 / MU1438): install, `RESTORE` and
re-install from the SD card passed, and Ukrainian works in the MMI menus. Other
cars and firmware versions are untested. This is not a claim of complete
translation of every reachable screen.

### Free distribution and installation

The author provides this mod **completely free of charge to everyone**.
Downloading, using and installing the localization must remain free. You may
install it yourself or help another vehicle owner install it free of charge.

**Selling, reselling or making money from this mod is prohibited.** Charging for
the package, access to it, installation or activation is not permitted, nor is
including it in paid bundles, services or commercial offerings.
When sharing it free of charge, retain these terms, author attribution and a link
to the [original repository](https://github.com/yety-ua/mhi2-ukrainian-localization).

These terms apply to this project's original contributions. M.I.B. and third-party
resources retain their own licenses and terms, which this repository does not change.

### Coverage and exact target

- **22 target modules; 15,400 original nonempty slots plus one Ukrainian language-name slot.**
- `uk_UA` language menu entry, flag, builtin config and reviewed `2D00` parameterization.
- MMI rotary/touch **alphabet band with all 33 Ukrainian letters**, including `Ґ Є І Ї`,
  Cyrillic default and no `Ё Ъ Ы Э`. It is an alphabet band, not a QWERTY layout.
- Exact train/MU/HMI verification, checksums, persistence CRCs, baseline copies on
  SD and the unit, read-back and independent restoration.
- Optional **English** NAVI/TTS/SDS routing in a separate install/reboot cycle;
  no Ukrainian speech recognition or Ukrainian voice assets.

Only `MHI2_ER_AUG22_K3346`, MU1438, G22/MLB Evo,
`HMI_AU_MIB2_H_EU_G22_C6_190300` / EvoHigh are supported.
Details, evidence and the check list: [which cars the package fits](docs/COMPATIBILITY.md).
A3 AU37x/P5089, MHI2Q, MIB3 and different firmware/MU versions are rejected.
A3 supplied additional dictionary translations matched by the **A4 source text**;
its table IDs, layout, classes and vehicle coding were not transplanted.
[Provenance evidence and limitations](docs/A4_PROVENANCE.md).

Source resources and emulator evidence were checked against the A4 B9 baseline.
The model list applies to this exact firmware, not every MMI fitted to these models.
Other models must also match the reviewed stock resources and datasets; the installer
stops on a mismatch. Separate physical-vehicle trials for these models are pending.

### Screenshots

The gallery above contains owner-captured, screen-only K3346 emulator screenshots
from 2026-10-13: main menu, language selection, phone, sound and MMI settings.
They are UI evidence, not vehicle acceptance. They precede the nine Connectivity-only
publication text fixes; none of the shown modules changed. Some emulated widget
rendering is incomplete. [Capture provenance](docs/screenshots.json).

### Quick install

1. Download the `.zip` from [Releases](https://github.com/yety-ua/mhi2-ukrainian-localization/releases).
2. M.I.B. must already be installed (its full folder on SD1). Unpack the archive and copy the **contents** of its `mod/` folder into the existing `mod/` on the card (do not replace `mod` itself).
3. Insert the card in SD1 → GEM → `m.i.b.` → `Advanced Settings` → **`Run individual script`**.
4. **Read the end of the output:** it shows the status and what to do next. Run the same item again until you see `SUCCESS` (for each action, two runs show a checklist and the third executes).
   - Fresh unit: `CHECK PASS` → `INSTALL`.
   - An earlier version of this package is installed: `CHECK` offers `RESTORE` → then `CHECK` → `INSTALL`.
5. After `SUCCESS: INSTALL` switch the ignition fully off (doors, lock, 3-5 minutes) and on. Choose "Українська" in Settings > MMI > Language.

**First time with M.I.B.?** There is a separate [step-by-step guide](docs/INSTALL_GUIDE.md#english): glossary, safety net (telnet, backups), and what to do when something goes wrong.
Verified: install, `RESTORE` and re-install from the SD card on one car (A4 B9, K3346 / MU1438, 2026-10-31). Other cars and versions are untested.

### Restore

If something goes wrong, or you want the original back: run the same GEM item (`Run individual script`); `CHECK` offers `RESTORE`, executed by the third consecutive run. An interrupted write is rolled back automatically (`ROLLED BACK`). Detailed steps, the telnet fallback and the `ACTION.txt` reference are in the [detailed guide](docs/INSTALL_GUIDE.md#reference-english).

### Localization depth and limits

[Coverage review](docs/LOCALIZATION_DEPTH.md) describes keyboard, handwriting, fonts,
navigation, voice, VC and remaining editorial work. The native handwriting engine
remains ru_RU; alphabet display does not prove all Ukrainian stroke recognition.
VC0313 receives no new Ukrainian resource bank from this package. Brands, numbers,
supported English commands, diagnostics and region-specific strings are not all
expected to be Cyrillic; candidate counts are not a translation-completeness percentage.

### Ukrainian in Virtual Cockpit

**Ukrainian MMI does not automatically make the cluster Ukrainian.** VC uses its
own language resources; this SD overlay never installs or flashes VC firmware.

| Models / VC family | VC software | Preliminary result |
| --- | --- | --- |
| A4/A5/Q5, AU491 | **0313** | **No native Ukrainian from this package:** stock VC rejects language code 43 |
| A4/A5/Q5, AU491 | **0379** | **Works on a car:** protocol/resources confirmed; on an A4 B9 (cluster 8W5 920 790 D, H15, SW 0379, updated from 0313) Ukrainian is shown in the cluster, 2026-10-31 |
| Q7, AU736 | **0310** | **No native Ukrainian from this package:** inspected binary rejects language code 43 |
| Q7, AU736 | **0378** | **Language support confirmed in protocol/resources** by native binary inspection |
| Q7, AU736 | **0416** | **Language support confirmed in protocol/resources** by native binary inspection |

**H15 is not a proven blanket blocker for 0379**, but compass results after updates
conflict. A higher H revision is not universal compatibility approval either.
[Full sourced VC research](docs/VC_COMPATIBILITY.md) separates native language support,
hardware/update eligibility, compass and Q7/TPMS behavior. Use complete module-17
HW/SW identifiers, H revision, software, model year and region. Language support in
0378/0416 does not approve installation on every Q7: physical display, hardware and
equipment compatibility remain separate tests.

### Development / Розробка

**Технічна примітка щодо ACTION.txt:** готовий файл уже має потрібний формат.
Якщо редагуєте його для зміни режиму, зберігайте лише одне слово дії, без пробілів,
у ASCII або UTF-8 без BOM, з переносом LF. Це вимога скрипта, не окрема дія перед CHECK.

**Technical note on ACTION.txt:** the supplied file already has the required format.
When editing it to change modes, retain a single action word without whitespace,
ASCII or UTF-8 without BOM, and LF line endings. No format conversion is needed before CHECK.

```sh
python3 -m unittest discover -s tests -v
UK_TEST_SHELL=oksh python3 -m unittest discover -s tests   # also mksh: the unit's /bin/sh is a pdksh
python3 tools/audit_resources.py --output docs/resource-audit.json
sh -n sd-card/mod/custom.sh sd-card/mod/command.sh sd-card/mod/uk-localization/scripts/localization.sh
python3 tools/package_release.py
```

The packaging tool refuses existing output; use `--output` with a fresh filename.
Runtime checks use M.I.B.'s SHA-1 utility; package metadata and the release sidecar
also use SHA-256. Checksums detect transfer corruption, not authenticity signatures.
The released hook is the production hook, never the emulator timeout override.

### References / Джерела

[M.I.B.](https://github.com/Mr-MIBonk/M.I.B._More-Incredible-Bash),
[GEM custom entry](https://github.com/Mr-MIBonk/M.I.B._More-Incredible-Bash/blob/0e041895a1ce36da4cb0835437d48aa5dbbf262a/esd/scripts/custom.sh),
[GEM menu](https://github.com/Mr-MIBonk/M.I.B._More-Incredible-Bash/blob/0e041895a1ce36da4cb0835437d48aa5dbbf262a/esd/Launcher-sda0.esd),
[tools/node routing](https://github.com/Mr-MIBonk/M.I.B._More-Incredible-Bash/blob/0e041895a1ce36da4cb0835437d48aa5dbbf262a/config/GLOBALS),
[language parameterization](https://github.com/Mr-MIBonk/M.I.B._More-Incredible-Bash/blob/0e041895a1ce36da4cb0835437d48aa5dbbf262a/apps/setlang).

This is an independent localization project. Firmware-derived resources retain
their existing third-party provenance; no Audi approval/signature is implied.
