/// Convert a byte buffer into a UI-friendly string.
///
/// - Valid UTF-8 → original string
/// - Otherwise → `"<binary N bytes: HHHH…>"` where HHHH is a short hex preview.
///
/// This keeps value display binary-safe without changing serialized shapes
/// expected by the frontend.
pub fn bytes_to_display_string(bytes: &[u8]) -> String {
    match std::str::from_utf8(bytes) {
        Ok(s) => s.to_string(),
        Err(_) => {
            let len = bytes.len();
            let preview_len = bytes.len().min(32);
            let hex: String = bytes[..preview_len]
                .iter()
                .map(|b| format!("{:02x}", b))
                .collect();
            let suffix = if len > preview_len { "…" } else { "" };
            format!("<binary {} bytes: {}{}>", len, hex, suffix)
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_utf8() {
        let bytes = "hello world".as_bytes().to_vec();
        assert_eq!(bytes_to_display_string(&bytes), "hello world");
    }

    #[test]
    fn test_chinese() {
        let bytes = "你好".as_bytes().to_vec();
        assert_eq!(bytes_to_display_string(&bytes), "你好");
    }

    #[test]
    fn test_binary() {
        let bytes = vec![0x80, 0x81, 0x82];
        let out = bytes_to_display_string(&bytes);
        assert!(out.starts_with("<binary 3 bytes: "));
        assert!(out.contains("808182"));
    }

    #[test]
    fn test_binary_truncated() {
        let bytes: Vec<u8> = (0..200).map(|i| (i % 256) as u8).collect();
        let out = bytes_to_display_string(&bytes);
        assert!(out.starts_with("<binary 200 bytes: "));
        assert!(out.ends_with("…>"));
    }
}
