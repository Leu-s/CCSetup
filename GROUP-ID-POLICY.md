# Group ID policy

## Призначення політики

Пакет розділяє два різні поняття:
- **logical project identity**
- **storage namespace identity**

## 1. Logical group id

Це людиночитний ідентифікатор проекту:
```text
MEMORY_GROUP_ID: verbalium/mobile-app
```

Він:
- читається людьми
- живе в `CLAUDE.md`
- не повинен мінятися через rename каталогу
- має відображати project identity, а не випадковий локальний шлях

## 2. Storage group id

Це технічний namespace, який реально використовується hooks і Graphiti ingest path:
```text
GRAPHITI_STORAGE_GROUP_ID: g_verbalium_mobile_app_abcd1234efgh5678
```

Він:
- генерується детерміновано
- є ASCII-safe
- не вводиться вручну
- не призначений для читання людиною як основна project label

## 3. Нормалізація logical id

Перед обчисленням storage id logical id:
- нормалізується в Unicode NFKC
- обрізається по краях
- схлопує повторні пробіли

Це прибирає тихі дублікати на кшталт:
- `repo`
- `repo `
- `repo   `
- compatibility-символів, що виглядають однаково

## 4. Формат storage id

```text
g_<slug>_<hash>
```

Де:
- `slug` — ASCII-варіант logical id
- `hash` — короткий base32 від SHA-256 канонізованого logical id

## 5. Пріоритет джерел

Під час runtime пакет працює в такому порядку:
1. registry mapping
2. `GRAPHITI_STORAGE_GROUP_ID` у `CLAUDE.md`
3. детермінований expected storage id

### Практичний наслідок
Після bootstrap registry стає канонічним local record для repo memory identity.

## 6. Bootstrap policy

Під час bootstrap:
- logical id нормалізується
- обчислюється canonical storage id
- у `CLAUDE.md` пишуться обидва значення
- у registry записується mapping

Якщо використано `--keep-existing-storage-id`, пакет:
- зберігає наявний storage id
- фіксує його в registry як effective storage id
- окремо пам'ятає `expected_storage_group_id`

## 7. Що таке drift

Drift є, якщо:
- storage id у `CLAUDE.md` не збігається з registry або expected
- registry знає інший storage id для того самого logical id
- кілька logical ids ведуть на один storage id

## 8. Як поводитися при rename

### Якщо проект той самий
Logical id не змінюй.

### Якщо identity справді змінилася
Використай один із двох режимів:

#### `keep-storage`
Зберігає старий storage namespace.
Підходить, якщо це той самий проект, просто з новою людською назвою.

#### `new-storage`
Створює новий storage namespace.
Підходить, якщо це справді нова memory line.

## 9. Команди для свідомої зміни identity

### Зберегти storage id
```bash
./tools/graphiti_admin.py migrate-logical-id /absolute/path/to/repo \
  --new-logical-group-id verbalium/mobile \
  --mode keep-storage
```

### Створити новий storage id
```bash
./tools/graphiti_admin.py migrate-logical-id /absolute/path/to/repo \
  --new-logical-group-id verbalium/mobile-v2 \
  --mode new-storage
```

## 10. Чого не треба робити

- не використовуй raw logical id як backend namespace
- не підправляй storage id руками “для краси”
- не заводь два logical ids для одного проекту без свідомої policy
- не змішуй backend-профілі для однієї memory line без migration plan
