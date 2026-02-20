### 生产环境已经有的服务

| CONTAINER ID | IMAGE | COMMAND | CREATED | STATUS | PORTS | NAMES |
|--------------|-------|---------|---------|--------|-------|-------|
| b5e5bc544209 | quantmeta:latest | "/docker-entrypoint.…" | 5 days ago | Up 5 days | 0.0.0.0:80->80/tcp, [::]:80->80/tcp | quantmeta |
| 80b10f82a6aa | redis:7-alpine | "docker-entrypoint.s…" | 6 days ago | Up 6 days | 0.0.0.0:6379->6379/tcp, [::]:6379->6379/tcp | redis |
| 77767e910dbf | timescale/timescaledb:latest-pg15 | "docker-entrypoint.s…" | 6 days ago | Up 6 days | 0.0.0.0:5432->5432/tcp, [::]:5432->5432/tcp | postgres-timescaledb |
| 5e6adbaa576c | apache/kafka:latest | "/__cacert_entrypoin…" | 6 days ago | Up 6 days | 0.0.0.0:9092->9092/tcp, [::]:9092->9092/tcp | kafka |
| 2f4a2d6c08cd | minio/minio:latest | "/usr/bin/docker-ent…" | 6 days ago | Up 6 days | 0.0.0.0:9000-9001->9000-9001/tcp, [::]:9000-9001->9000-9001/tcp | minio |

