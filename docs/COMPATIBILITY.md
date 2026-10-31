# Яких автомобілів стосується пакет / Which cars the package fits

[Українська](#українська) · [English](#english) · [← README](../README.md)

## Українська

Коротко: **пакет не знає про модель авто. Він пускає запис лише в блок, де збігається все
перевірене нижче.** Тож питання «чи підійде моя машина» зводиться до питання «чи збігається
мій блок з перевіреним зразком». Це можна дізнатися без ризику: запуск `CHECK` нічого не змінює.

### Що перевіряє інсталятор (усе має збігтися, інакше запису не буде)

| # | Перевірка | Навіщо |
| --- | --- | --- |
| 1 | Образ HMI `/ifs/lsd.jxe` збігається з перевіреним (SHA-1 `9a22e891…46132e5f`, SHA-256 `e43d80e7…974b99ce`) | Це точна збірка `HMI_AU_MIB2_H_EU_G22_C6_190300`; наші ресурси й hook зібрані саме під неї |
| 2 | Потяг `MHI2_ER_AUG22_K3346…` і MU `1438`, якщо їх вдалося прочитати (файли `CachedTrain.txt`/`CachedMuVersion.txt`, запасно EEPROM) | Друга думка. Якщо прочитати не вдалося, лише попередження: рішення тримається на п. 1 |
| 3 | Мовні файли блока (`lang_data.zip`, `lang_hmi_builtin.config`, `language_lut_hmi.txt`, прапорець `1100066.png`) збігаються з оригіналами в `stock/` | Не затираємо чужі зміни |
| 4 | Набори даних персистенції `2D00` і `0x280` збігаються з оригіналами | Те саме для списку мов |
| 5 | Немає наших чи чужих `lang_uk_hook.jar`, `lang_uk_voice.jar`, `1100076.png`; є папка `HMISettingsEvoHigh` | Невідомі модифікації зупиняють встановлення |
| 6 | ≥ 40 000 КіБ вільного в `/mnt/app`, M.I.B. не виконує бекап/перезавантаження | Безпека запису |

Номера моделі, VIN чи комплектації скрипт не читає й не використовує.

### Підтверджено і не підтверджено

| Що | Статус | Доказ |
| --- | --- | --- |
| **Audi A4 B9 (2016), MMI з `MHI2_ER_AUG22_K3346`, MU1438** | **`CHECK PASS` на автомобілі** 2026-10-25. Сам запис (`INSTALL`) ще не виконувався | Лог `run-….log` з карти: усі п. 1–6 пройдено, у т. ч. оригінальні набори даних |
| A5, Q5, Q7 з **тим самим потягом K3346/MU1438** | Очікується, але **на цих авто не перевірялось** | Таблиця прошивок M.I.B. зараховує `MHI2_ER_AUG22_K3346_MU1438` до `A4/A5/Q5/Q7` (Audi, EU): це одна збірка ПЗ; а п. 1 вимагає байт-у-байт той самий образ HMI |
| Блоки K3344/MU1438 | **Не підтримується (поки що)**: образ HMI там байт-у-байт той самий (SHA-256 `e43d80e7…` у профілі aberbic), але потяг відхиляється, а мовні файли й набори даних K3344 ми не перевіряли | Профіль `mu1438.json` (K3344) проєкту aberbic; M.I.B.: K3344 і K3346 — окремі потяги |
| Інші потяги Audi A4/A5/Q5/Q7: K3241/MU0678, K2161/MU1421, S2148/MU0442 | Відхиляються (інший образ HMI) | Для P3241/MU0678 HMI `…_160601`, не `…_190300` |
| США (K3345/K3347, MU1439), Китай, Японія, MHI2Q (потяги `P…`) | Відхиляються | Інші потяги/MU |
| A3 (AU37x), Q2, TT, R8, A6/A7/A8, а також VW, Škoda, SEAT, Porsche, Bentley | Відхиляються | Інші потяги (`AU37x`, `AU276`, `AU43x`, `AU57x`, …) |

**Набір даних 2D00 не залежить від одного автомобіля.** Оригінал у пакеті (19 мов, без `uk_UA`)
дослівно збігається зі штатним європейським набором, який M.I.B. (`apps/setlang`, тег V3.7.1)
записує для `MHI2_ER_AUG22*`. Тож немодифіковані європейські блоки цього потягу його матимуть.
Блок, у якому список мов змінювали (власник чи майстер), інсталятор відхилить на п. 4.

### Чого не дає цей аналіз

- Фізично перевірено лише один автомобіль. «A5/Q5/Q7» це висновок із ідентичності прошивки, а не
  випробування на тих авто.
- Нас цікавить лише мовна частина MMI. Панель приладів (Virtual Cockpit) має власні мовні
  ресурси й окрему сумісність: [огляд VC](VC_COMPATIBILITY.md). Інші проєкти на цій прошивці
  теж перевіряли лише A4 B9, а геометрія панелі в інших кузовах може відрізнятися (це стосується
  кокпіта, а не нашого пакета).
- Таблиця M.I.B. фіксує, які прошивки тестувались із M.I.B. (прошивка, патчі), а не мовні
  модифікації.

### Як перевірити своє авто без ризику

1. Підготуйте карту за [посібником](INSTALL_GUIDE.md) і один раз запустіть пункт GEM (`CHECK`).
   Він нічого не встановлює.
2. `CHECK PASS` означає, що ваш блок збігається з перевіреним зразком за п. 1–6.
   Помилка означає, що пакет туди не підходить; нічого не змінено.
3. Якщо ваш блок інший, ми можемо розглянути його окремо: надішліть фото екрана і вміст
   `mod/uk-localization/logs/`. Нові потяги додаються лише після порівняння їхніх файлів і наборів даних.

## English

In short: **the package knows nothing about the car model. It only allows a write to a unit
where everything checked below matches.** So "does my car fit" becomes "does my unit match the
reviewed sample", which can be tested at no risk: `CHECK` changes nothing.

### What the installer verifies (all must match, or nothing is written)

| # | Check | Why |
| --- | --- | --- |
| 1 | The HMI image `/ifs/lsd.jxe` equals the reviewed one (SHA-1 `9a22e891…46132e5f`, SHA-256 `e43d80e7…974b99ce`) | It is the exact `HMI_AU_MIB2_H_EU_G22_C6_190300` build our resources and hook were made for |
| 2 | Train `MHI2_ER_AUG22_K3346…` and MU `1438`, when readable (`CachedTrain.txt`/`CachedMuVersion.txt`, then EEPROM) | A second opinion. If unreadable it is only a warning; the decision rests on #1 |
| 3 | The unit's language files (`lang_data.zip`, `lang_hmi_builtin.config`, `language_lut_hmi.txt`, flag `1100066.png`) equal the originals in `stock/` | We never overwrite someone else's changes |
| 4 | The persistence datasets `2D00` and `0x280` equal the originals | Same for the language list |
| 5 | No `lang_uk_hook.jar`, `lang_uk_voice.jar`, `1100076.png` present; the `HMISettingsEvoHigh` folder exists | Unknown modifications stop the install |
| 6 | ≥ 40,000 KiB free in `/mnt/app`; no M.I.B. backup/reboot running | Write safety |

The script never reads or uses a model name, VIN or equipment code.

### Confirmed and unconfirmed

| What | Status | Evidence |
| --- | --- | --- |
| **Audi A4 B9 (2016), MMI `MHI2_ER_AUG22_K3346`, MU1438** | **`CHECK PASS` on the car**, 2026-10-25. The write itself (`INSTALL`) has not run yet | The card's `run-….log`: checks 1–6 all passed, including the original datasets |
| A5, Q5, Q7 with the **same train K3346/MU1438** | Expected, but **not tested on those cars** | M.I.B.'s FW table lists `MHI2_ER_AUG22_K3346_MU1438` for `A4/A5/Q5/Q7` (Audi, EU): one software build; and #1 demands the byte-identical HMI image |
| K3344/MU1438 units | **Not supported (yet)**: the HMI image there is byte-identical (SHA-256 `e43d80e7…` in aberbic's profile) but the train is refused, and K3344's language files and datasets were not reviewed | aberbic's `mu1438.json` profile (K3344); M.I.B. treats K3344 and K3346 as separate trains |
| Other A4/A5/Q5/Q7 trains: K3241/MU0678, K2161/MU1421, S2148/MU0442 | Refused (different HMI image) | P3241/MU0678 carries HMI `…_160601`, not `…_190300` |
| US (K3345/K3347, MU1439), China, Japan, MHI2Q (`P…` trains) | Refused | Different trains/MUs |
| A3 (AU37x), Q2, TT, R8, A6/A7/A8, and VW, Škoda, SEAT, Porsche, Bentley | Refused | Other trains (`AU37x`, `AU276`, `AU43x`, `AU57x`, …) |

**The 2D00 dataset is not specific to one car.** The package's original (19 languages, no
`uk_UA`) is word for word the stock European dataset that M.I.B. (`apps/setlang`, tag V3.7.1)
writes for `MHI2_ER_AUG22*`. Unmodified European units of this train will carry it. A unit whose
language list was changed (by the owner or a workshop) is refused at #4.

### What this analysis does not give

- Only one car has been tested physically. "A5/Q5/Q7" is an inference from firmware identity,
  not a trial on those cars.
- Only the MMI language side is covered. The instrument cluster (Virtual Cockpit) has its own
  language resources and compatibility: [VC overview](VC_COMPATIBILITY.md). Other projects on this
  firmware have also tested A4 B9 only, and cluster geometry may differ on other bodies (that
  concerns the cluster, not this package).
- M.I.B.'s table records which firmwares were tested with M.I.B. (flashing, patches), not
  language mods.

### How to test your car at no risk

1. Prepare the card per the [guide](INSTALL_GUIDE.md) and run the GEM item once (`CHECK`). It installs nothing.
2. `CHECK PASS` means your unit matches the reviewed sample on #1–6. An error means the package
   does not fit; nothing was changed.
3. If your unit differs, we can look at it separately: send a photo of the screen and the
   contents of `mod/uk-localization/logs/`. New trains are added only after their files and datasets
   are compared.

Sources: [M.I.B. FW compatibility table](https://github.com/Mr-MIBonk/M.I.B._More-Incredible-Bash/wiki/MHI2-M.I.B.-patch-FW-compatibility-table),
[M.I.B. `apps/setlang` V3.7.1](https://github.com/Mr-MIBonk/M.I.B._More-Incredible-Bash/blob/V3.7.1/apps/setlang),
[aberbic `profiles/mu1438.json`](https://github.com/aberbic/Audi-MHI2-Virtual-Cockpit-Altscreen-CarPlay-AndroidAuto/blob/main/profiles/mu1438.json),
and the owner's own unit data (`CHECK PASS` log, harvest listings).
