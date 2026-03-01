# Arm Imposter — Խաղ Impostor հայերեն

Մобильном խաղ (Python + Kivy): մեկ խաղացող Impostor, մնացածը տեսնում են գաղտնի բառը, հուշումներով ու քվեարկությամբ պետք է բացահայտել Impostor-ին։

## Ինչպես խաղալ

1. **Սկսել խաղը** — գլխավոր մենյուից։
2. **Ընտրել կատեգորիա** — Հայ հայտնիներ, Համաշխարհային հայտնիներ, Կենդանիներ, Առարկաներ, Վայրեր կամ Բոլորը։
3. **Կարգավորումներ** — մասնակիցների քանակ (3–15), Impostor-ների քանակ, ռաունդի ժամանակ (թայմեր)։
4. **Ցույց տալ** — յուրաքանչյուր խաղացող հերթով տեսնում է իր խաղաքարտը (բառ կամ «IMPOSTOR»)։
5. **Ռաունդ** — խոսակցություն 1–2 բառանոց հուշումներով, ապա **Քվեարկություն**։
6. Եթե քվեարկությունը բացահայտում է Impostor-ին — **թիմը հաղթում է**, եթե ոչ — **Impostor-ը հաղթում է**։

## Տեղադրում (desktop)

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install kivy
# Ընտրովի՝ blur-ի համար
pip install Pillow
```

Նկարներ՝ `assets/` պանակում դրեք **logo.JPG** և **menu.JPG** (մանրամասն՝ assets/README.txt):

```bash
python main.py
```

## Браузер (веб-версия) — для клиента

### GitHub Pages (игра по ссылке для клиента)

1. Создайте репозиторий на GitHub и загрузите проект (или он уже есть).
2. В репозитории: **Settings** → **Pages**.
3. В блоке **Build and deployment** выберите:
   - **Source**: Deploy from a branch
   - **Branch**: `main` (или `master`)
   - **Folder**: `/docs`
4. Нажмите **Save**. Через 1–2 минуты игра будет доступна по адресу:
   - `https://ВАШ_ЛОГИН.github.io/ИМЯ_РЕПОЗИТОРИЯ/`

Игра лежит в папке **docs/** (она уже настроена для GitHub Pages). Клиенту можно просто отправить эту ссылку.

### Локальный просмотр

Запустите сервер в папке **web**:
```bash
cd web && python3 -m http.server 8080
```
Откройте `http://localhost:8080`. Подробнее: **web/README.md**.

## Android (APK)

1. Տեղադրել [Buildozer](https://buildozer.readthedocs.io/) (Linux/Mac).
2. Պրոյեկտի պանակում.
   ```bash
   buildozer android debug
   ```
3. APK կլինի `bin/` պանակում։ Google Play-ում հրապարակելու համար կարող եք կառուցել release և ստորագրել։

## iOS (App Store)

Kivy-ի [iOS packaging](https://kivy.org/doc/stable/guide/packaging-ios.html) — օգտագործել **kivy-ios** (սովորաբար Mac + Xcode):

```bash
pip install kivy-ios
toolchain build python3 kivy
# Ապա Xcode project և archive for App Store
```

## Խաղի չափ

Էկրանը կարգավորված է բջջային պորտրետ ռեժիմի համար (360×640 dp); tablet/desktop-ում պատուհանը կարող եք ձգել։

## Ֆայլեր

- `main.py` — Kivy հավելված, բոլոր էկրանները և լոգիկան։
- `data/words_hy.json` — հայերեն բառեր կատեգորիաներով (200–200)։
- `assets/` — logo.JPG, menu.JPG (և ավտոմատ menu_blur.JPG)։

## Լիցենզիա

Ծրագիրը պատրաստված է անձնական/ուսումնական օգտագործման համար։ App Store / Google Play-ում հրապարակելու համար հետևեք Apple-ի և Google-ի քաղաքականություններին։
