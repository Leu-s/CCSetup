# File tree

```text
.
├── README.md
├── TUTORIAL.md
├── GLOBAL-BASELINE.md
├── STACK-DECISIONS.md
├── QUICKSTART.md
├── INSTALL.md
├── USER-MANUAL.md
├── HOOKS.md
├── OPERATIONS.md
├── TROUBLESHOOTING.md
├── ARCHITECTURE.md
├── GROUP-ID-POLICY.md
├── SECURITY.md
├── CONFIG-REFERENCE.md
├── CLI-REFERENCE.md
├── SUPPORT-MATRIX.md
├── ops/
│   ├── docker-compose.graphiti-neo4j.yml
│   ├── docker-compose.graphiti-falkordb.yml
│   ├── graphiti-mcp.Dockerfile
│   ├── env/
│   │   ├── graphiti.neo4j.env.example
│   │   └── graphiti.falkordb.env.example
│   ├── config/
│   │   ├── config-docker-neo4j.openai.yaml
│   │   ├── config-docker-falkordb.openai.yaml
│   │   ├── config-docker-neo4j.gemini.yaml
│   │   └── config-docker-falkordb.gemini.yaml
│   ├── examples/
│   │   ├── mcp.graphiti.remote-bearer.example.json
│   │   └── mcp.graphiti.remote-headers-helper.example.json
│   ├── systemd/
│   │   ├── graphiti-flush@.service
│   │   └── graphiti-flush@.timer
│   └── caddy/
│       └── graphiti.Caddyfile
├── templates/
│   └── project/
│       ├── CLAUDE.md
│       ├── .mcp.graphiti.fragment.json
│       └── .claude/
│           ├── graphiti.json
│           ├── settings.graphiti.fragment.json
│           ├── rules/
│           │   └── graphiti-memory.md
│           ├── state/
│           │   └── .gitignore
│           └── hooks/
│               ├── run_python.sh
│               ├── instructions_loaded.py
│               ├── session_start.py
│               ├── cwd_changed.py
│               ├── file_changed.py
│               ├── pre_compact.py
│               ├── graphiti_stop.py
│               ├── graphiti_flush.py
│               ├── graphiti_doctor.py
│               ├── graphiti_status.py
│               ├── graphiti_requeue.py
│               ├── config_drift_guard.py
│               └── lib/
│                   ├── __init__.py
│                   ├── adapters.py
│                   ├── capture.py
│                   ├── config.py
│                   ├── group_ids.py
│                   ├── ledger.py
│                   ├── observability.py
│                   ├── queue_store.py
│                   ├── runtime.py
│                   └── util.py
├── tools/
│   ├── baseline_doctor.py
│   ├── configure-codebase-memory.sh
│   ├── graphiti_bootstrap.py
│   ├── install-hook-runtime.sh
│   ├── install-graphiti-stack.sh
│   ├── graphiti_admin.py
│   └── validate-package.py
└── tests/
    ├── run-tests.sh
    ├── test_group_ids.py
    ├── test_admin_wrapper.py
    ├── test_baseline_doctor.py
    ├── test_bootstrap_hygiene.py
    ├── test_install_flow_offline.py
    ├── test_e2e_mock.py
    └── test_hook_contracts.py
```
