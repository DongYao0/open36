#!/bin/bash
# ─────────────────────────────────────────────────────────────
#  Open436 生产部署前置检查
#  任何检查失败都返回非零退出码，且不再打印"建议改 0.0.0.0"。
# ─────────────────────────────────────────────────────────────
set -euo pipefail

PROD_DIR="$(cd "$(dirname "$0")/.." && pwd)"
ENV_FILE="$PROD_DIR/.env.production"
EXAMPLE_FILE="$PROD_DIR/.env.production.example"
FAIL=0

echo "== Open436 生产部署前置检查 =="

# ───────────── 1) .env 必须存在 ─────────────
if [ ! -f "$ENV_FILE" ]; then
  echo "[FAIL] 未找到 $ENV_FILE"
  echo "       请执行："
  echo "       cp $EXAMPLE_FILE $ENV_FILE"
  echo "       然后用强随机密钥替换所有 CHANGE_ME_* 占位符。"
  FAIL=1
else
  echo "[OK] 生产环境变量文件存在: $ENV_FILE"
fi

# ───────────── 2) 占位密钥必须全部替换 ─────────────
if [ -f "$ENV_FILE" ]; then
  PLACEHOLDERS=$(grep -E '^[[:space:]]*[A-Z_]+=.*CHANGE_ME' "$ENV_FILE" | wc -l || true)
  if [ "${PLACEHOLDERS:-0}" -gt 0 ]; then
    echo "[FAIL] $ENV_FILE 中仍有 ${PLACEHOLDERS} 个 CHANGE_ME_* 占位符未替换"
    grep -nE '^[[:space:]]*[A-Z_]+=.*CHANGE_ME' "$ENV_FILE" | head -10 | sed 's/^/        /'
    FAIL=1
  else
    echo "[OK] 所有占位密钥已替换"
  fi

  # ───────────── 3) 所有生产关键变量必填 ─────────────
  REQUIRED_VARS="POSTGRES_USER POSTGRES_PASSWORD POSTGRES_DB REDIS_PASSWORD
    MINIO_ROOT_USER MINIO_ROOT_PASSWORD MINIO_BUCKET HOJ_MYSQL_ROOT_PASSWORD
    NACOS_USERNAME NACOS_PASSWORD DJANGO_SECRET_KEY INTERNAL_API_KEY HOJ_API_KEY
    JUDGE_TOKEN HOJ_JWT_SECRET HOJ_ADMIN_USER HOJ_ADMIN_PASS ADMIN_BOOTSTRAP_USER
    ADMIN_BOOTSTRAP_PASSWORD_HASH ADMIN_BIND_IP ADMIN_BIND_PORT"
  for must in $REQUIRED_VARS; do
    VAL=$(grep -E "^${must}=" "$ENV_FILE" | cut -d= -f2- | tr -d '"' | tr -d "'" || true)
    if [ -z "${VAL:-}" ]; then
      echo "[FAIL] $must 必须设置（生产环境不可留空）"
      FAIL=1
    elif echo "${VAL:-}" | grep -q "CHANGE_ME"; then
      echo "[FAIL] $must 仍为占位符"
      FAIL=1
    fi
  done
  if [ $FAIL -eq 0 ]; then
    echo "[OK] 所有生产关键变量均已设置"
  fi

  # PostgreSQL/Redis 密码会直接嵌入连接 URL，必须使用 RFC 3986 unreserved 字符。
  for url_password in POSTGRES_PASSWORD REDIS_PASSWORD; do
    VAL=$(grep -E "^${url_password}=" "$ENV_FILE" | cut -d= -f2- | tr -d '"' | tr -d "'" || true)
    if ! printf '%s' "$VAL" | grep -Eq '^[A-Za-z0-9._~-]+$'; then
      echo "[FAIL] $url_password 含 URL 保留字符；请使用 openssl rand -hex 32"
      FAIL=1
    fi
  done

  DJANGO_KEY=$(grep -E '^DJANGO_SECRET_KEY=' "$ENV_FILE" | cut -d= -f2- | tr -d '"' | tr -d "'" || true)
  if [ "${#DJANGO_KEY}" -lt 50 ]; then
    echo "[FAIL] DJANGO_SECRET_KEY 长度必须至少为 50 个字符"
    FAIL=1
  fi
fi

# ───────────── 4) Admin 绑定 IP 必须真实存在于本机网卡 ─────────────
ADMIN_IP=""
ADMIN_PORT=""
if [ -f "$ENV_FILE" ]; then
  ADMIN_IP="$(grep -E '^ADMIN_BIND_IP=' "$ENV_FILE" | cut -d= -f2- | tr -d '"' | tr -d "'")"
  ADMIN_PORT="$(grep -E '^ADMIN_BIND_PORT=' "$ENV_FILE" | cut -d= -f2- | tr -d '"' | tr -d "'")"
fi

echo ""
echo "== Admin 绑定地址检测 =="
echo "  目标绑定: ${ADMIN_IP:-<未设置>}:${ADMIN_PORT:-<未设置>} -> 容器 80"

# 严禁 0.0.0.0 / localhost
case "${ADMIN_IP:-}" in
  ""|0.0.0.0|127.0.0.1|localhost)
    echo "[FAIL] ADMIN_BIND_IP 不得为 0.0.0.0 / localhost（会暴露到所有网卡且违反最小权限）"
    echo "       请改为实验室网卡真实 IP（执行 ip addr 查看）。"
    FAIL=1
    ;;
esac

# Linux: 真实检测本机网卡
if command -v ip >/dev/null 2>&1 && [ -n "${ADMIN_IP:-}" ]; then
  if ip -o addr show | awk '{print $4}' | cut -d/ -f1 | grep -qx "${ADMIN_IP}"; then
    echo "  [OK] 本机网卡存在 ${ADMIN_IP}"
  else
    echo "[FAIL] 本机网卡未发现 ${ADMIN_IP}，docker compose up 将立即报错"
    echo "       候选 IP（任选其一填入 ADMIN_BIND_IP）："
    ip -o addr show | awk '$2 != "lo" {print $4}' | cut -d/ -f1 | head -5 | sed 's/^/         /'
    FAIL=1
  fi
elif [ -n "${ADMIN_IP:-}" ] && [ "${ADMIN_IP}" != "0.0.0.0" ] && [ "${ADMIN_IP}" != "localhost" ]; then
  echo "  [INFO] 非 Linux（无法用 ip 自动检测），请手动确认 ${ADMIN_IP} 已挂载"
  echo "         Windows: ipconfig；macOS: ifconfig"
fi

echo ""
if [ $FAIL -ne 0 ]; then
  echo "== 前置检查失败：exit 1 =="
  exit 1
fi
echo "== 前置检查通过 =="
