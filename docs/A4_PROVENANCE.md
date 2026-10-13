# Походження A4 / A4 terminology and provenance

## Українська

Ціль — `MHI2_ER_AUG22_K3346 / MU1438`, G22/MLB Evo, EvoHigh,
`HMI_AU_MIB2_H_EU_G22_C6_190300`. Перевірка 13.10.2026 виконана за реальним
штатним K3346 `app.img`, збереженими оригіналами з автомобіля та релізним пакетом.
Повний образ прошивки, дані автомобіля й журнали не включені до цього репозиторію.

### Підтверджено

- Усі **420 ZIP-записів** `stock/lang_data.zip` побайтово збігаються з мовним
  архівом саме K3346 `extract/MMX2/app/50/default/app.img`. SHA-256 базового ZIP:
  `82558f1e6808f9f27a6c1f0102f8421c9aac86c9498a928b7d76428de54991cf`.
- Українські таблиці будуються в **22 модулях A4 EvoHigh**, зі штатними слотами,
  прапорцями, порожніми позиціями, розміткою й параметрами `%1/%2/...`.
  Єдина додана позиція — назва мови в HMISettingsEvoHigh; решта штатних мов збережена.
- Production hooks зібрані для K3346 `lsd.jxe`, SHA-256
  `e43d80e7eeb803d6a7db29908562b9545e7b17138d4660ce3a6efafa974b99ce`.
  Інсталятор вимагає точного live HMI fingerprint, train і MU.
- `2D00` — оригінал A4 плюс `uk_UA:01`; штатні 19 мов і решта полів збережені.
  Кодування автомобіля, KZB/layout, native binaries, CarPlay та конфігурація A3
  не переносяться цим пакетом.
- Пошук модельних маркерів `A3/AU37x/AU370/G21/Sportback/e-tron/magnetic ride`
  не знайшов A3/G21/AU370/Sportback/magnetic ride в українських текстах.
  Дев'ять знайдених згадок `e-tron` уже є у відповідних оригінальних слотах K3346;
  це спільні штатні ресурси комплектацій, а не доказ перенесення меню A3.

### Яку роль відігравала A3

Основне джерело українського словника — споріднена A4/G22 MHI2Q.
A3 `MHI2_ER_AU37x_P5089` також використовувалася як **додатковий словник** і як
приклад інтеграції мови. Історичне формулювання «A3 лише приклад інтеграції» було
неповним: її тексти теж використовувалися там, де збігався оригінальний текст.

Алгоритм брав текст **цільового слоту K3346**, шукав відповідний англійський текст
у джерелах (точно, з нормалізацією пробілів або регістру) і підставляв переклад.
Це не копіювання таблиці A3 за номером: номери й розміри модулів між платформами різні.
Додатково застосовані власні переклади, скорочення й наступні редакційні правки.
Збіг вихідної фрази не гарантує однакового контексту в кожному модулі, тому потрібний
контекстний перегляд термінів; автоматичні перевірки не сертифікують всю семантику.

Для геометричних бюджетів A3 EvoHighScale не використовувалася як доказ придатності
до A4 EvoHigh; підтримку розміру оцінювали за цільовими мовами й донором того самого
скіна. Це евристика довжини, а не доказ вміщення кожного напису на екрані.

### Приклад перевірки терміна за A4

`sichtbar/unsichtbar` — слоти 586/587 HMIConnectivityEvoHigh, ID `2500586/2500587`.
У штатному K3346 класі `ConnectivityScreenBag1.cMMAIN` вони належать label моделі
`2500231`. `de.audi.app.bluetooth.evo.accessibility.Accessibility` пов'язує цю модель
з видимістю Bluetooth: 0 — видимий, 1 — невидимий, 2 — вимкнений.
Тому українські «Видимий / Невидимий / Вимкнено» відповідають саме A4 K3346.
Поруч виправлені «Точка доступу», «Режим модема», «Без мережі / У мережі» та WLAN → Wi-Fi.
[Точний маніфест правок](connectivity-review-2026-10-13.json).

## English

The target is the original Audi A4 B9 K3346/MU1438 G22/MLB Evo/EvoHigh firmware.
On 2026-10-13, all **420 stock language ZIP entries** were compared byte-for-byte
with the language archive extracted from that exact K3346 app.img. They match.
The firmware image and private vehicle evidence are not distributed in this repository.

All 22 Ukrainian module tables preserve the A4's slots, flags, empty positions,
formatting and placeholders. Stock locales are unchanged except the appended
Ukrainian language name. Production classes target the K3346 lsd.jxe fingerprint
shown above. The installer checks real EEPROM train/MU and the exact live HMI binary.
Parameterization preserves the original A4 dataset and adds only uk_UA:01.
No A3 coding, layouts, native binaries, module ID tables or firmware are transplanted.

The historical translation dictionary used related A4/G22 MHI2Q resources first
and **A3 AU37x as an additional text dictionary**, plus manual overrides/reviews.
The A4 source text was the lookup key, with exact/whitespace-normalized/case-insensitive
matching; A3 table positions were not used as A4 IDs. Describing A3 only as an
integration example was incomplete. Identical source wording is still not an
exhaustive semantic-context guarantee, so contextual terminology review remains.
The A3 EvoHighScale skin was not accepted as evidence of A4 EvoHigh layout budgets.

No A3/AU37x/AU370/G21/Sportback/magnetic-ride tokens were found in released Ukrainian
strings. Nine e-tron references already exist in the corresponding K3346 source
slots. Shared equipment resource banks do not imply the user's A4 exposes every
listed feature. [Machine-readable model-token audit](resource-audit.json).

Bluetooth visibility was traced directly through K3346's Accessibility model
2500231 and cMMAIN text IDs 2500586–2500588 before translation. This is concrete
A4 context evidence, separate from dictionary matching. See the reviewed change
manifest. The token scan and structural audit do not certify every term's meaning
or every screen's visual fit.
