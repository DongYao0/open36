#!/bin/sh
# ─────────────────────────────────────────────────────────────
#  Open436 MinIO 幂等初始化
#  1) 等待 MinIO 就绪
#  2) 创建/确认 bucket：open436-posts
#  3) 配置匿名只读策略（FileService 通过同源 /objects/<bucket>/... 暴露文件）
#  重复运行幂等（mc mb --ignore-existing / mc anonymous set）
# ─────────────────────────────────────────────────────────────
set -eu

MINIO_ALIAS="${MINIO_ALIAS:-local}"
MINIO_ENDPOINT="${MINIO_ENDPOINT:-http://minio:9000}"
MINIO_ROOT_USER="${MINIO_ROOT_USER}"
MINIO_ROOT_PASSWORD="${MINIO_ROOT_PASSWORD}"
BUCKET="${MINIO_BUCKET:-open436-posts}"

echo "[minio-init] waiting for MinIO at ${MINIO_ENDPOINT} ..."
until mc alias set "$MINIO_ALIAS" "$MINIO_ENDPOINT" "$MINIO_ROOT_USER" "$MINIO_ROOT_PASSWORD" >/dev/null 2>&1; do
  echo "[minio-init] minio not ready, retrying..."
  sleep 2
done

echo "[minio-init] ensure bucket ${BUCKET}"
mc mb --ignore-existing "${MINIO_ALIAS}/${BUCKET}"

echo "[minio-init] set anonymous read on ${BUCKET}"
# 只读公开：允许匿名 GET 对象（FileService 返回的 URL 无签名，需匿名读）
mc anonymous set download "${MINIO_ALIAS}/${BUCKET}"

echo "[minio-init] done"
