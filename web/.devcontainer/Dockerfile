FROM mcr.microsoft.com/devcontainers/universal:2

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# ==============================================================================
# 更换 apt 镜像源（阿里云）
# ==============================================================================
RUN set -eux; \
    sed -i 's|deb.debian.org|mirrors.aliyun.com|g' /etc/apt/sources.list.d/debian.sources 2>/dev/null || true; \
    sed -i 's|deb.debian.org|mirrors.aliyun.com|g' /etc/apt/sources.list 2>/dev/null || true

# ==============================================================================
# 修复 Yarn APT 源的 NO_PUBKEY 问题
# 关键：基础镜像里可能已经有旧的 /etc/apt/sources.list.d/yarn.list，
# 会导致第一句 apt-get update 直接失败，所以必须先删掉
# ==============================================================================
RUN set -eux; \
    rm -f /etc/apt/sources.list.d/yarn.list; \
    \
    apt-get update; \
    apt-get install -y --no-install-recommends ca-certificates curl gnupg; \
    \
    mkdir -p /etc/apt/keyrings; \
    curl -fsSL https://dl.yarnpkg.com/debian/pubkey.gpg | gpg --dearmor -o /etc/apt/keyrings/yarn-archive-keyring.gpg; \
    \
    echo "deb [signed-by=/etc/apt/keyrings/yarn-archive-keyring.gpg] https://dl.yarnpkg.com/debian stable main" \
      > /etc/apt/sources.list.d/yarn.list; \
    \
    # 再次更新，验证 yarn 源不再报 NO_PUBKEY
    apt-get update; \
    rm -rf /var/lib/apt/lists/*

# ==============================================================================
# 安装系统依赖（LaTeX + 构建工具）
# ==============================================================================
RUN set -eux; \
    apt-get update; \
    apt-get install -y --no-install-recommends --fix-missing \
      curl \
      build-essential \
      unzip \
      texlive-latex-base \
      texlive-latex-recommended \
      texlive-latex-extra \
      texlive-fonts-recommended \
      texlive-pictures \
      latexmk; \
    rm -rf /var/lib/apt/lists/*
