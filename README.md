# 安全使用
## 方法一（推荐）：命令面板
Ctrl/Cmd + Shift + P
→ Codespaces: Stop Current Codespace

## 方法二：直接在 GitHub 网页上停
去 github.com/codespaces → 找到你的 Codespace → 点 ··· → Stop codespace



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
