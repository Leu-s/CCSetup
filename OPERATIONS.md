# Operations

## 1. Базові перевірки

```bash
./tools/graphiti_admin.py baseline-doctor /absolute/path/to/repo
./tools/graphiti_admin.py status /absolute/path/to/repo
./tools/graphiti_admin.py doctor /absolute/path/to/repo
```

## 2. Queue operations

```bash
./tools/graphiti_admin.py flush /absolute/path/to/repo --limit 20
./tools/graphiti_admin.py requeue /absolute/path/to/repo --source dead-letter --limit 20
```

## 3. Що не керується цим repo runtime

Global/plugin lifecycle для:
- ECC
- context-mode
- ui-ux-pro-max-skill

Вони керуються Claude Code plugin system або upstream installers.

## 4. Що тепер керується цим repo runtime

- Graphiti repo overlay
- queue / ledger / archive / dead-letter
- repo-declared plugin baseline
- `codebase-memory-mcp` first-run bootstrap

## 5. Scheduler boundary

Цей пакет не вимагає конкретного scheduler, але описує два recommended paths: systemd на Linux/WSL та cron на будь-якій Unix-подібній системі (macOS, Linux, WSL).

### 5.1 Linux / WSL via systemd

Шаблони юнітів лежать у `ops/systemd/`:
- `graphiti-flush@.service` викликає `./.claude/hooks/run_python.sh graphiti_flush.py --limit 50` у заданому repo;
- `graphiti-flush@.timer` спрацьовує кожні 2 хвилини (`OnUnitActiveSec=2m`) після першого старту через `OnBootSec=1m`.

Інсталяція як user units (instance name — escaped абсолютний шлях до repo, див. `systemd-escape`).

### 5.2 Cross-platform via cron

Якщо systemd недоступний (macOS, мінімальні Linux образи без user-systemd), cron-wrapper дає однаковий shape на всіх підтримуваних платформах.

Shape wrapper-скрипту `~/.claude/hooks/graphiti-flush-cron.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

# 1. Де лежить сам ccsetup clone — звідси запускається admin CLI.
CCSETUP_DIR="${CCSETUP_DIR:-$HOME/src/ccsetup}"

# 2. Секрети і env для graphiti_core: chmod 600, містить OPENAI_API_KEY,
#    NEO4J_PASSWORD, NEO4J_URI, GOOGLE_API_KEY тощо.
ENV_FILE="${GRAPHITI_CRON_ENV_FILE:-$HOME/.claude/graphiti.neo4j.env}"

# 3. Список repo, по одному абсолютному шляху на рядок, # коментарі та порожні рядки ігноруються.
REPOS_LIST="${GRAPHITI_CRON_REPOS_LIST:-$HOME/.claude/hooks/graphiti-flush-repos.list}"

# 4. Cron-specific лог у stable каталозі state.
LOG_DIR="${GRAPHITI_CRON_LOG_DIR:-$HOME/.claude/state}"
LOG_FILE="$LOG_DIR/cron-flush.log"
mkdir -p "$LOG_DIR"

# Завантажити env (chmod 600).
if [ -f "$ENV_FILE" ]; then
  set -a
  # shellcheck disable=SC1090
  . "$ENV_FILE"
  set +a
fi

cd "$CCSETUP_DIR"

timestamp() { date -u +"%Y-%m-%dT%H:%M:%SZ"; }

while IFS= read -r repo || [ -n "$repo" ]; do
  case "$repo" in ""|\#*) continue ;; esac
  echo "[$(timestamp)] flush $repo" >> "$LOG_FILE"
  ./tools/graphiti_admin.py flush "$repo" --limit 50 >> "$LOG_FILE" 2>&1 || \
    echo "[$(timestamp)] flush failed for $repo (rc=$?)" >> "$LOG_FILE"
done < "$REPOS_LIST"
```

Що робить:
- вантажить env з `~/.claude/graphiti.neo4j.env` (chmod 600, містить `OPENAI_API_KEY`, `NEO4J_PASSWORD`, `NEO4J_URI`, опційно `GOOGLE_API_KEY`);
- ітерує список repo з `~/.claude/hooks/graphiti-flush-repos.list` (один абсолютний шлях на рядок, `#`-коментарі і порожні рядки пропускаються);
- на кожен repo виконує `./tools/graphiti_admin.py flush <repo> --limit 50`;
- пише per-run лог у `~/.claude/state/cron-flush.log` (stdout+stderr per repo).

Приклад вмісту `~/.claude/hooks/graphiti-flush-repos.list`:

```text
# One absolute repo path per line.
/Users/you/src/verbalium-mobile-app
/Users/you/src/ccsetup
```

Приклад crontab (кожні 15 хвилин):

```cron
*/15 * * * * ~/.claude/hooks/graphiti-flush-cron.sh >> ~/.claude/state/cron-flush.log 2>&1
```

Права і послідовність:
- `chmod +x ~/.claude/hooks/graphiti-flush-cron.sh`;
- `chmod 600 ~/.claude/graphiti.neo4j.env`;
- `crontab -e` щоб додати рядок вище.

### 5.3 macOS Full Disk Access requirement

На сучасних macOS `/usr/sbin/cron` сам по собі не має доступу до приватних каталогів користувача (включно з `~/.claude/**` і багатьма repo під `~/Documents`, `~/Desktop`, external volumes). Без Full Disk Access (FDA) cron-джоб тихо провалюється на читанні protected paths — сам `cron` запускається, але wrapper не бачить env file, repos list або `.claude/state/`, і доставка мовчки не відбувається.

Як увімкнути FDA для cron:

1. відкрий `System Settings → Privacy & Security → Full Disk Access`;
2. натисни `+` і через Cmd+Shift+G додай `/usr/sbin/cron`;
3. увімкни тумблер для `cron`;
4. якщо редагуєш crontab через `crontab -e`, термінал (Terminal.app / iTerm) теж має бути у FDA — інакше редагування збережеться, але виконання не побачить protected paths.

Перевірка: після першого cron-fire лог `~/.claude/state/cron-flush.log` має містити рядок `flush <repo>` і не містити `Permission denied` / `Operation not permitted`.

### 5.4 Async flush via `Stop` hook

Альтернатива cron/systemd для latency-чутливих setups — `queue.asyncFlushOnStop=true` у `.claude/graphiti.json`. Тоді `Stop` після spool сам спавнить detached flush subprocess (див. `HOOKS.md` §6 і `CONFIG-REFERENCE.md` §5). Підходить, якщо хочеш бачити session summary у Neo4j майже одразу, без зовнішнього scheduler. Cron все одно лишається корисним як safety net для retry після мережевих збоїв і для repo, з якими давно не було сесій.

### 5.5 Scheduler boundary (EN)

The package does not mandate a specific scheduler. Two supported paths:

- **Linux / WSL via systemd** — templates in `ops/systemd/` (`graphiti-flush@.service` + `graphiti-flush@.timer`, 2-minute interval).
- **Cross-platform via cron** — wrapper at `~/.claude/hooks/graphiti-flush-cron.sh` (shape above) that loads `~/.claude/graphiti.neo4j.env`, iterates `~/.claude/hooks/graphiti-flush-repos.list`, runs `./tools/graphiti_admin.py flush <repo> --limit 50` per entry, and logs to `~/.claude/state/cron-flush.log`. Sample crontab: `*/15 * * * * ~/.claude/hooks/graphiti-flush-cron.sh >> ~/.claude/state/cron-flush.log 2>&1`.

On macOS, `/usr/sbin/cron` must be granted Full Disk Access via `System Settings → Privacy & Security → Full Disk Access`. Without FDA, the cron process runs but cannot read protected paths (env file, repos list, `.claude/state/**`), and flushes fail silently. The terminal app used to edit crontab should also have FDA.

As a latency-sensitive alternative, enable `queue.asyncFlushOnStop=true` in `.claude/graphiti.json` so the `Stop` hook spawns a detached flush off the session-end critical path — see `HOOKS.md` and `CONFIG-REFERENCE.md`. Cron still helps as a safety net for retries and cold repos.
