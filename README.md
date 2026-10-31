# 🇺🇦 Ukrainian localization for Audi MHI2 — A4 / A5 / Q5 / Q7

**MHI2_ER_AUG22_K3346 · MU1438 · G22 · EvoHigh**

[Українська](#українська) · [English](#english) · [Покрокова інструкція / Step-by-step guide](docs/INSTALL_GUIDE.md) · [Download / Завантажити](https://github.com/yety-ua/mhi2-ukrainian-localization/releases) · [Глибина / Coverage](docs/LOCALIZATION_DEPTH.md) · [A4 provenance](docs/A4_PROVENANCE.md)

![Українське головне меню Audi A4 K3346 / Ukrainian Audi A4 K3346 main menu](docs/images/main-menu.png)

## Українська

Українська локалізація для штатної прошивки **Audi MHI2 K3346 на A4, A5, Q5 та Q7**: українські тексти меню, вибір мови з прапорцем, українська клавіатура. Встановлюється з SD-карти через [M.I.B.](https://github.com/Mr-MIBonk/M.I.B._More-Incredible-Bash); прошивка не перепрошивається, оригінал можна повернути (`RESTORE`).

**Перевірено на одному авто** (A4 B9, K3346 / MU1438): встановлення, `RESTORE` і повторне встановлення з SD пройшли, українська працює в меню MMI. Інші авто й версії прошивки не перевірялися. Не всі екрани й команди перекладено ([що саме](docs/LOCALIZATION_DEPTH.md)).

### Швидке встановлення

1. Завантажте з [Releases](https://github.com/yety-ua/mhi2-ukrainian-localization/releases) файл `.zip`.
2. M.I.B. вже має стояти в голові (повний M.I.B. лежить на SD1). Розпакуйте архів і скопіюйте **вміст** його теки `mod/` у наявну `mod/` на SD-карті (саму теку `mod` не замінюйте).
3. Вставте карту в SD1 → GEM → `m.i.b.` → `Advanced Settings` → **`Run individual script`**.
4. **Читайте кінець виводу:** там статус і підказка, що робити далі. Повторюйте той самий пункт, доки не побачите `SUCCESS` (кожна дія: два запуски показують чеклист, третій виконує).
   - Нова голова: `CHECK PASS` → `INSTALL`.
   - Уже стоїть попередня версія пакета: `CHECK` запропонує `RESTORE` → потім `CHECK` → `INSTALL`.
5. Після `SUCCESS: INSTALL` повністю вимкніть запалювання (двері, замок, 3–5 хвилин) і ввімкніть. Виберіть «Українська» в Налаштування → MMI → Мова.

**Вперше з M.I.B.?** [Покрокова інструкція](docs/INSTALL_GUIDE.md#українська): словник, страховка (telnet, резервні копії), що робити, якщо щось пішло не так.
**Щось пішло не так?** Запустіть той самий пункт: `CHECK` запропонує `RESTORE` (третій запуск поспіль). Запис, що перервався, інсталятор відкочує сам (`ROLLED BACK`). Докладно: [довідка](docs/INSTALL_GUIDE.md#довідка-українська).

### Що включено

- Український інтерфейс MMI (22 модулі, понад 15 000 рядків), вибір мови з прапорцем.
- Клавіатура: 33 українські літери (смуга для ручки/тачпада, не QWERTY), кирилиця за замовчуванням.
- Перевірка точної прошивки й контрольних сум, резервні копії на SD та в голові, автоматичний відкат.
- Необов'язково й окремо: англійський fallback для навігації/голосу. Українського голосу й розпізнавання мовлення немає.

### Сумісність

Лише `MHI2_ER_AUG22_K3346`, MU `1438`, HMI `HMI_AU_MIB2_H_EU_G22_C6_190300` (G22 / MLB Evo; A4, A5, Q5, Q7). Потрібні M.I.B. V3.6+ (на авто пробувалась V3.7.1) і SD-карта FAT32 у **SD1** (повнорозмірна, від 4 ГБ, без захисту від запису).
Інші MHI2 (зокрема A3 AU37x/P5089), MHI2Q, MIB3 та інші версії MU не підтримуються: інсталятор звіряє точний хеш образу HMI й зупиняється при розбіжності. Докладно: [яких авто стосується пакет](docs/COMPATIBILITY.md), [походження ресурсів](docs/A4_PROVENANCE.md).

### Українська у Virtual Cockpit

Українська в MMI не означає автоматично українську в кокпіті: панель приладів має власні мовні ресурси, цей пакет їх не встановлює й VC не перепрошиває.

| Авто / гілка VC | Версія VC | Результат |
| --- | --- | --- |
| A4/A5/Q5, AU491 | **0313** | Українську не підхопить: штатна версія відхиляє код мови 43 |
| A4/A5/Q5, AU491 | **0379** | **Працює на авто:** на A4 B9 (блок 8W5 920 790 D, H15, ПЗ 0379, оновлено з 0313) українська показується в кокпіті, 2026-10-31 |
| Q7, AU736 | **0310** | Українську не підхопить: бінарник відхиляє код мови 43 |
| Q7, AU736 | **0378**, **0416** | Мовна підтримка є за аналізом бінарників; на авто не перевірено |

H15 не є автоматичною забороною для 0379, але результати роботи компаса після оновлення суперечливі. Не вибирайте прошивку лише за номером версії. [Повне дослідження VC](docs/VC_COMPATIBILITY.md).

### Безкоштовне поширення

Автор поширює мод **безкоштовно для всіх**. **Продаж, перепродаж і заробіток заборонені**: не можна брати плату за пакет, доступ до нього, встановлення чи активацію або включати його в платні пакети й послуги. При поширенні зберігайте ці умови, авторство й посилання на [репозиторій](https://github.com/yety-ua/mhi2-ukrainian-localization). M.I.B. і ресурси третіх сторін мають власні ліцензії.

Ще: [скріншоти](docs/SCREENSHOTS.md) · [глибина локалізації](docs/LOCALIZATION_DEPTH.md) · [розробка й джерела](docs/DEVELOPMENT.md)

## English

A Ukrainian localization for the stock **Audi MHI2 K3346 firmware on A4, A5, Q5 and Q7**: Ukrainian menu texts, a language entry with flag, and a Ukrainian keyboard. It installs from an SD card through [M.I.B.](https://github.com/Mr-MIBonk/M.I.B._More-Incredible-Bash); no firmware flash, and the original can be restored (`RESTORE`).

**Verified on one car** (A4 B9, K3346 / MU1438): install, `RESTORE` and re-install from the SD card passed, and Ukrainian works in the MMI menus. Other cars and firmware versions are untested. Not every screen and command is translated ([details](docs/LOCALIZATION_DEPTH.md)).

### Quick install

1. Download the `.zip` from [Releases](https://github.com/yety-ua/mhi2-ukrainian-localization/releases).
2. M.I.B. must already be installed (its full folder on SD1). Unpack the archive and copy the **contents** of its `mod/` folder into the existing `mod/` on the card (do not replace `mod` itself).
3. Insert the card in SD1 → GEM → `m.i.b.` → `Advanced Settings` → **`Run individual script`**.
4. **Read the end of the output:** it shows the status and what to do next. Run the same item again until you see `SUCCESS` (for each action, two runs show a checklist and the third executes).
   - Fresh unit: `CHECK PASS` → `INSTALL`.
   - An earlier version of this package is installed: `CHECK` offers `RESTORE` → then `CHECK` → `INSTALL`.
5. After `SUCCESS: INSTALL` switch the ignition fully off (doors, lock, 3-5 minutes) and on. Choose "Українська" in Settings > MMI > Language.

**First time with M.I.B.?** [Step-by-step guide](docs/INSTALL_GUIDE.md#english): glossary, safety net (telnet, backups), troubleshooting.
**Something went wrong?** Run the same item: `CHECK` offers `RESTORE` (third consecutive run). An interrupted write is rolled back automatically (`ROLLED BACK`). Details: [reference](docs/INSTALL_GUIDE.md#reference-english).

### What is included

- Ukrainian MMI interface (22 modules, over 15,000 strings) with a language entry and flag.
- Keyboard: 33 Ukrainian letters (an alphabet band for the rotary/touch controller, not QWERTY), Cyrillic by default.
- Exact firmware and checksum verification, backups on the SD and the unit, automatic rollback.
- Optional and separate: English fallback for navigation/voice. No Ukrainian voice or speech recognition.

### Compatibility

Only `MHI2_ER_AUG22_K3346`, MU `1438`, HMI `HMI_AU_MIB2_H_EU_G22_C6_190300` (G22 / MLB Evo; A4, A5, Q5, Q7). Needs M.I.B. V3.6+ (V3.7.1 was tried on the car) and a FAT32 SD card in **SD1** (full-size, 4 GB or more, not write-protected).
Other MHI2 (including A3 AU37x/P5089), MHI2Q, MIB3 and other MU versions are not supported: the installer checks the exact HMI image hash and stops on a mismatch. Details: [which cars the package fits](docs/COMPATIBILITY.md), [provenance](docs/A4_PROVENANCE.md).

### Ukrainian in Virtual Cockpit

Ukrainian MMI does not automatically make the cluster Ukrainian: the cluster has its own language resources, this package neither installs them nor flashes VC firmware.

| Models / VC family | VC software | Result |
| --- | --- | --- |
| A4/A5/Q5, AU491 | **0313** | No native Ukrainian: stock VC rejects language code 43 |
| A4/A5/Q5, AU491 | **0379** | **Works on a car:** on an A4 B9 (cluster 8W5 920 790 D, H15, SW 0379, updated from 0313) Ukrainian is shown in the cluster, 2026-10-31 |
| Q7, AU736 | **0310** | No native Ukrainian: inspected binary rejects language code 43 |
| Q7, AU736 | **0378**, **0416** | Language support found in binary analysis; not tested on a car |

H15 is not a proven blocker for 0379, but compass results after updates conflict. Do not pick firmware by version number alone. [Full VC research](docs/VC_COMPATIBILITY.md).

### Free distribution

The mod is provided **free of charge to everyone**. **Selling, reselling or making money from it is prohibited**: no charging for the package, access, installation or activation, and no inclusion in paid bundles or services. When sharing, keep these terms, attribution and a link to the [repository](https://github.com/yety-ua/mhi2-ukrainian-localization). M.I.B. and third-party resources keep their own licenses.

More: [screenshots](docs/SCREENSHOTS.md) · [localization depth](docs/LOCALIZATION_DEPTH.md) · [development and references](docs/DEVELOPMENT.md)
