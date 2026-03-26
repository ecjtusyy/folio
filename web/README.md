# Monorepo Notes + Blog + Imports (M1/M2/M3)

## Quick Start (WSL2)

```bash
mkdir -p /mnt/d/app-data /mnt/d/app-data/tmp /mnt/d/app-data/logs
mkdir -p /mnt/d/cache/pip /mnt/d/cache/npm

cp deploy/.env.example deploy/.env

bash deploy/up.sh
bash deploy/verify_all.sh
```

## URLs
- Web: http://localhost
- API health: http://localhost/api/health
- OnlyOffice health: http://localhost/onlyoffice/healthcheck
