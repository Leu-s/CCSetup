# Group ID policy

## Purpose of this policy

The package separates two distinct concepts:
- **logical project identity**
- **storage namespace identity**

## 1. Logical group id

This is the human-readable project identifier:
```text
MEMORY_GROUP_ID: verbalium/mobile-app
```

It:
- is read by humans
- lives in `CLAUDE.md`
- must not change on directory rename
- must reflect project identity, not an incidental local path

## 2. Storage group id

This is the technical namespace actually used by hooks and the Graphiti ingest path:
```text
GRAPHITI_STORAGE_GROUP_ID: g_verbalium_mobile_app_abcd1234efgh5678
```

It:
- is generated deterministically
- is ASCII-safe
- must not be entered by hand
- is not intended as the primary human-facing project label

## 3. Logical id normalization

Before the storage id is computed, the logical id is:
- normalized to Unicode NFKC
- trimmed at the edges
- collapsed on repeated whitespace

This removes silent duplicates such as:
- `repo`
- `repo `
- `repo   `
- compatibility characters that look identical

## 4. Storage id format

```text
g_<slug>_<hash>
```

Where:
- `slug` is the ASCII variant of the logical id
- `hash` is a short base32 of SHA-256 over the canonicalized logical id

## 5. Source priority

At runtime the package resolves in this order:
1. registry mapping
2. `GRAPHITI_STORAGE_GROUP_ID` in `CLAUDE.md`
3. deterministic expected storage id

### Practical consequence
After bootstrap, the registry becomes the canonical local record for a repo's memory identity.

## 6. Bootstrap policy

During bootstrap:
- the logical id is normalized
- the canonical storage id is computed
- both values are written to `CLAUDE.md`
- the mapping is written to the registry

If `--keep-existing-storage-id` is used, the package:
- preserves the existing storage id
- records it in the registry as the effective storage id
- separately remembers `expected_storage_group_id`

## 7. What drift is

Drift exists when:
- the storage id in `CLAUDE.md` does not match the registry or expected value
- the registry knows a different storage id for the same logical id
- multiple logical ids point to the same storage id

## 8. How to handle renames

### If it is the same project
Do not change the logical id.

### If the identity really changed
Use one of the two modes:

#### `keep-storage`
Preserves the old storage namespace.
Appropriate when it is the same project, just with a new human-facing name.

#### `new-storage`
Creates a new storage namespace.
Appropriate when it is genuinely a new memory line.

## 9. Commands for deliberate identity changes

### Preserve the storage id
```bash
./tools/graphiti_admin.py migrate-logical-id /absolute/path/to/repo \
  --new-logical-group-id verbalium/mobile \
  --mode keep-storage
```

### Create a new storage id
```bash
./tools/graphiti_admin.py migrate-logical-id /absolute/path/to/repo \
  --new-logical-group-id verbalium/mobile-v2 \
  --mode new-storage
```

## 10. What not to do

- do not use the raw logical id as a backend namespace
- do not hand-edit the storage id "for aesthetics"
- do not create two logical ids for the same project without a deliberate policy
- do not mix backend profiles for a single memory line without a migration plan
