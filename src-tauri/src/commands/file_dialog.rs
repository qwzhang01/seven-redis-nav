use crate::error::{IpcError, IpcResult};

/// Open a native file picker dialog. Returns the selected file path, or null if cancelled.
#[tauri::command]
pub async fn dialog_open_file(filters: Option<Vec<FileFilter>>) -> IpcResult<Option<String>> {
    let mut dialog = rfd::AsyncFileDialog::new();
    if let Some(fs) = filters {
        for f in &fs {
            let exts: Vec<&str> = f.extensions.iter().map(|s| s.as_str()).collect();
            dialog = dialog.add_filter(&f.name, &exts);
        }
    }
    let result = dialog.pick_file().await;
    Ok(result.map(|h| h.path().to_string_lossy().to_string()))
}

/// Open a native save dialog. Returns the chosen save path, or null if cancelled.
#[tauri::command]
pub async fn dialog_save_file(
    default_name: Option<String>,
    filters: Option<Vec<FileFilter>>,
) -> IpcResult<Option<String>> {
    let mut dialog = rfd::AsyncFileDialog::new();
    if let Some(name) = &default_name {
        dialog = dialog.set_file_name(name);
    }
    if let Some(fs) = filters {
        for f in &fs {
            let exts: Vec<&str> = f.extensions.iter().map(|s| s.as_str()).collect();
            dialog = dialog.add_filter(&f.name, &exts);
        }
    }
    let result = dialog.save_file().await;
    Ok(result.map(|h| h.path().to_string_lossy().to_string()))
}

/// Read a text file from the given path.
#[tauri::command]
pub async fn fs_read_text_file(path: String) -> IpcResult<String> {
    tokio::fs::read_to_string(&path)
        .await
        .map_err(|e| IpcError::Internal { message: format!("读取文件失败: {e}") })
}

/// Write text content to the given path.
#[tauri::command]
pub async fn fs_write_text_file(path: String, content: String) -> IpcResult<()> {
    tokio::fs::write(&path, content.as_bytes())
        .await
        .map_err(|e| IpcError::Internal { message: format!("写入文件失败: {e}") })
}

#[derive(serde::Deserialize)]
pub struct FileFilter {
    pub name: String,
    pub extensions: Vec<String>,
}
