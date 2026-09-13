use sqlx::postgres::{PgPool, PgPoolOptions};
use std::time::Duration;

fn env_u32(key: &str, default: u32) -> u32 {
    std::env::var(key).ok().and_then(|v| v.parse().ok()).unwrap_or(default)
}

/// 创建数据库连接池（阶段7：上限经 FILE_DB_MAX_CONNECTIONS / FILE_DB_MIN_CONNECTIONS 配置，
/// 默认 20/5，纳入 PostgreSQL 总连接预算）
pub async fn create_pool(database_url: &str) -> PgPool {
    PgPoolOptions::new()
        .max_connections(env_u32("FILE_DB_MAX_CONNECTIONS", 20))
        .min_connections(env_u32("FILE_DB_MIN_CONNECTIONS", 5))
        .acquire_timeout(Duration::from_secs(5))
        .idle_timeout(Duration::from_secs(600))
        .connect(database_url)
        .await
        .expect("Failed to create database pool")
}

/// 健康检查：验证数据库连接
pub async fn health_check(pool: &PgPool) -> Result<(), sqlx::Error> {
    sqlx::query("SELECT 1")
        .execute(pool)
        .await?;
    Ok(())
}

