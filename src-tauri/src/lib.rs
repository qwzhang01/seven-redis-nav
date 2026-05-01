mod commands;
pub mod error;
pub mod models;
pub mod services;
mod utils;

use tauri::Emitter;
use commands::connection::{
    connection_test, connection_open, connection_close,
    connection_save, connection_list, connection_delete, connection_open_temp, db_select,
    connection_test_ssh, connection_test_tls,
    connection_test_sentinel, connection_test_cluster,
    connection_export, connection_import,
};
use commands::data::{keys_scan, key_get, key_set, key_delete, key_rename, key_ttl_set, keys_bulk_delete, keys_bulk_ttl};
use commands::terminal::{cli_exec, cli_history_get};
use commands::pubsub::{pubsub_subscribe, pubsub_unsubscribe, pubsub_publish};
use commands::monitor::{monitor_start, monitor_stop, monitor_metrics_start, monitor_metrics_stop};
use commands::server_config::{slowlog_get, slowlog_reset, config_get_all, config_set, server_info, config_rewrite, config_resetstat, config_get_notify_keyspace_events};
use commands::stream::{stream_range, stream_rev_range, stream_add, stream_del, stream_groups, stream_pending, stream_info};
use commands::bitmap::{bitmap_chunk, bitmap_count, bitmap_pos, bitmap_set_bit};
use commands::hll::{hll_add, hll_count, hll_merge};
// Phase 4
use commands::lua::{lua_eval, lua_evalsha, lua_script_load, lua_script_exists, lua_history_save, lua_history_list, lua_history_delete, lua_history_rename};
use commands::import_export::{export_keys_json, export_db_json, import_keys_json, rdb_parse_file};
use commands::tools::{
    key_scan_memory_start, key_scan_memory_stop, key_ttl_distribution, key_scan_memory_export_csv,
    health_check_generate, health_check_history_list, health_check_history_get, health_check_export_markdown,
    masking_rule_list, masking_rule_save, masking_rule_delete, masking_rule_reorder,
    shortcut_binding_list, shortcut_binding_save, shortcut_binding_delete, shortcut_binding_reset_all,
};
use commands::cli_tab::{cli_tab_create, cli_tab_close, cli_exec_tab, cli_history_get_tab};
use commands::file_dialog::{dialog_open_file, dialog_save_file, fs_read_text_file, fs_write_text_file};
use services::connection_manager::new_shared_manager;
use services::pubsub::new_shared_pubsub_manager;
use services::monitor::new_shared_monitor_manager;
use services::key_analyzer::{new_scan_registry, new_scan_results};
use services::cli_session_manager::{new_shared_cli_session_manager, collect_idle_tabs, mark_tab_disconnected};
use tauri::Manager;

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    // Initialize structured logging
    tracing_subscriber::fmt()
        .with_env_filter(
            tracing_subscriber::EnvFilter::try_from_default_env()
                .unwrap_or_else(|_| tracing_subscriber::EnvFilter::new("info")),
        )
        .init();

    tracing::info!("Seven Redis Nav starting...");

    let manager = new_shared_manager();
    let pubsub_manager = new_shared_pubsub_manager();
    let monitor_manager = new_shared_monitor_manager();
    let scan_registry = new_scan_registry();
    let scan_results = new_scan_results();
    let cli_session_manager = new_shared_cli_session_manager();

    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .setup(move |app| {
            let handle = app.handle().clone();
            let mgr = manager.clone();

            // Initialize SQLite — create a temporary runtime since setup runs
            // on the main thread without a tokio reactor on macOS
            let rt = tokio::runtime::Runtime::new()
                .expect("Failed to create tokio runtime for DB init");
            let db_pool = rt.block_on(async {
                utils::db::init_db(&handle).await.expect("Failed to initialize database")
            });
            drop(rt);

            app.manage(db_pool);
            app.manage(mgr.clone());
            app.manage(pubsub_manager.clone());
            app.manage(monitor_manager.clone());
            app.manage(scan_registry.clone());
            app.manage(scan_results.clone());
            app.manage(cli_session_manager.clone());

            // Start heartbeat (uses tauri::async_runtime internally)
            services::heartbeat::start_heartbeat(handle.clone(), mgr);

            // Start CLI idle tab cleanup task (30-minute timeout)
            let cli_mgr_for_idle = cli_session_manager.clone();
            let handle_for_idle = handle.clone();
            tauri::async_runtime::spawn(async move {
                loop {
                    tokio::time::sleep(tokio::time::Duration::from_secs(60)).await;
                    let idle_tabs = collect_idle_tabs(&cli_mgr_for_idle).await;
                    for tab_id in idle_tabs {
                        mark_tab_disconnected(&cli_mgr_for_idle, &tab_id).await;
                        let _ = handle_for_idle.emit("cli:tab_disconnected", serde_json::json!({ "tab_id": tab_id }));
                    }
                }
            });

            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            connection_test,
            connection_open,
            connection_open_temp,
            connection_close,
            connection_save,
            connection_list,
            connection_delete,
            db_select,
            connection_test_ssh,
            connection_test_tls,
            connection_test_sentinel,
            connection_test_cluster,
            connection_export,
            connection_import,
            keys_scan,
            key_get,
            key_set,
            key_delete,
            key_rename,
            key_ttl_set,
            keys_bulk_delete,
            keys_bulk_ttl,
            cli_exec,
            cli_history_get,
            pubsub_subscribe,
            pubsub_unsubscribe,
            pubsub_publish,
            monitor_start,
            monitor_stop,
            monitor_metrics_start,
            monitor_metrics_stop,
            slowlog_get,
            slowlog_reset,
            config_get_all,
            config_set,
            server_info,
            config_rewrite,
            config_resetstat,
            config_get_notify_keyspace_events,
            stream_range,
            stream_rev_range,
            stream_add,
            stream_del,
            stream_groups,
            stream_pending,
            stream_info,
            bitmap_chunk,
            bitmap_count,
            bitmap_pos,
            bitmap_set_bit,
            hll_add,
            hll_count,
            hll_merge,
            // Phase 4: Lua
            lua_eval,
            lua_evalsha,
            lua_script_load,
            lua_script_exists,
            lua_history_save,
            lua_history_list,
            lua_history_delete,
            lua_history_rename,
            // Phase 4: Import/Export
            export_keys_json,
            export_db_json,
            import_keys_json,
            rdb_parse_file,
            // Phase 4: Key Analyzer
            key_scan_memory_start,
            key_scan_memory_stop,
            key_ttl_distribution,
            key_scan_memory_export_csv,
            // Phase 4: Health Check
            health_check_generate,
            health_check_history_list,
            health_check_history_get,
            health_check_export_markdown,
            // Phase 4: Data Masking
            masking_rule_list,
            masking_rule_save,
            masking_rule_delete,
            masking_rule_reorder,
            // Phase 4: Shortcut Bindings
            shortcut_binding_list,
            shortcut_binding_save,
            shortcut_binding_delete,
            shortcut_binding_reset_all,
            // Phase 4: Multi-Tab CLI
            cli_tab_create,
            cli_tab_close,
            cli_exec_tab,
            cli_history_get_tab,
            // File Dialog & FS
            dialog_open_file,
            dialog_save_file,
            fs_read_text_file,
            fs_write_text_file,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
