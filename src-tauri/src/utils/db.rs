use sqlx::{sqlite::SqlitePoolOptions, SqlitePool};
use std::path::PathBuf;
use tauri::Manager;

/// Initialize SQLite connection pool and run migrations.
pub async fn init_db(app: &tauri::AppHandle) -> Result<SqlitePool, sqlx::Error> {
    let data_dir: PathBuf = app
        .path()
        .app_data_dir()
        .expect("failed to get app data dir");

    std::fs::create_dir_all(&data_dir).expect("failed to create app data dir");

    let db_path = data_dir.join("redis_nav.db");
    let db_url = format!("sqlite://{}?mode=rwc", db_path.to_string_lossy());

    tracing::info!(db_path = %db_path.display(), "Opening SQLite database");

    let pool = SqlitePoolOptions::new()
        .max_connections(5)
        .connect(&db_url)
        .await?;

    // Run embedded migrations
    sqlx::migrate!("./migrations").run(&pool).await?;

    tracing::info!("SQLite migrations applied successfully");
    Ok(pool)
}
