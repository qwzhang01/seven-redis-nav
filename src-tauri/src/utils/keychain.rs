//! macOS Keychain helpers with Touch ID / biometric support.
//!
//! ## Why we bypass `security_framework::passwords`
//!
//! The high-level `set_generic_password` / `get_generic_password` helpers do
//! not support `kSecAttrAccessControl` or `kSecUseAuthenticationUI`, so we
//! call the raw Security framework APIs directly.
//!
//! ## Write path (`save_password`)
//!   1. Delete any existing entry — `SecItemUpdate` cannot change
//!      `kSecAttrAccessControl` on an existing item.
//!   2. Build a `SecAccessControl` with:
//!      - protection = `kSecAttrAccessibleWhenPasscodeSetThisDeviceOnly`
//!        (required; without this, `BIOMETRY_ANY` is silently ignored on macOS)
//!      - flags     = `BIOMETRY_ANY | OR | DEVICE_PASSCODE`
//!   3. `SecItemAdd` with that access control attached.
//!
//! ## Read path (`get_password`)
//!   Build the query manually and add `kSecUseAuthenticationUI = allow`
//!   so the OS shows the Touch ID sheet before returning the data.

use core_foundation::base::{kCFAllocatorDefault, CFOptionFlags, TCFType};
use core_foundation::boolean::CFBoolean;
use core_foundation::data::CFData;
use core_foundation::dictionary::CFDictionary;
use core_foundation::number::CFNumber;
use core_foundation::string::CFString;
use core_foundation_sys::base::{CFGetTypeID, CFRelease, CFTypeRef};
use core_foundation_sys::data::CFDataRef;
use security_framework::access_control::SecAccessControl;
use security_framework::passwords_options::AccessControlOptions;
use security_framework_sys::access_control::{
    kSecAttrAccessibleWhenPasscodeSetThisDeviceOnly, SecAccessControlCreateWithFlags,
};
use security_framework_sys::base::errSecItemNotFound;
use security_framework_sys::item::{
    kSecAttrAccessControl, kSecAttrAccount, kSecAttrService, kSecClass,
    kSecClassGenericPassword, kSecMatchLimit, kSecReturnData,
    kSecUseAuthenticationUI, kSecUseDataProtectionKeychain, kSecValueData,
};
use security_framework_sys::keychain_item::{SecItemAdd, SecItemCopyMatching, SecItemDelete};
use std::ptr;
const SERVICE: &str = "seven-redis-nav";

// ─── helpers ────────────────────────────────────────────────────────────────

/// Wrap a raw `CFStringRef` constant into a `CFString` (get rule = no extra retain).
macro_rules! cf_str {
    ($raw:expr) => {
        unsafe { CFString::wrap_under_get_rule($raw) }
    };
}

/// Build the base query dict (class + service + account).
///
/// **`kSecUseDataProtectionKeychain = true` is critical on macOS.**
/// Without it, `SecItemAdd` stores the item in the "login keychain" which
/// does NOT support `kSecAttrAccessControl` / Touch ID — it only shows the
/// "Enter login keychain password" dialog instead.
fn base_query(account: &str) -> Vec<(CFString, core_foundation::base::CFType)> {
    vec![
        (cf_str!(kSecClass), cf_str!(kSecClassGenericPassword).into_CFType()),
        (cf_str!(kSecAttrService), CFString::from(SERVICE).into_CFType()),
        (cf_str!(kSecAttrAccount), CFString::from(account).into_CFType()),
        // Force data-protection keychain (iOS-style) — required for Touch ID.
        (cf_str!(kSecUseDataProtectionKeychain), CFBoolean::true_value().into_CFType()),
    ]
}

/// Create a `SecAccessControl` that requires Touch ID (any finger / Face ID)
/// OR device passcode.
///
/// **The `protection` parameter is mandatory on macOS.**  Passing `null` causes
/// the biometric constraint to be silently ignored.
fn make_biometric_access_control() -> Result<SecAccessControl, String> {
    let flags: CFOptionFlags = (AccessControlOptions::BIOMETRY_ANY
        | AccessControlOptions::OR
        | AccessControlOptions::DEVICE_PASSCODE)
        .bits();

    let ac = unsafe {
        SecAccessControlCreateWithFlags(
            kCFAllocatorDefault,
            // ← THIS is the fix: supply the protection value explicitly.
            kSecAttrAccessibleWhenPasscodeSetThisDeviceOnly.cast(),
            flags,
            ptr::null_mut(),
        )
    };

    if ac.is_null() {
        Err("SecAccessControlCreateWithFlags returned null".into())
    } else {
        Ok(unsafe { SecAccessControl::wrap_under_create_rule(ac) })
    }
}

// ─── public API ─────────────────────────────────────────────────────────────

/// Returns `true` if Touch ID / Face ID is available and enrolled.
#[allow(dead_code)]
pub fn is_biometric_available() -> bool {
    make_biometric_access_control().is_ok()
}

/// Save `password` for `account` in the Keychain, protected by Touch ID.
///
/// Any existing entry is deleted first (required to change access control).
///
/// Strategy:
///   1. Try data-protection keychain with biometric access control (production path).
///   2. If that fails with errSecMissingEntitlement (-34018), fall back to the
///      legacy login keychain without biometric protection.  This happens in
///      development mode where the app is not code-signed with entitlements.
pub fn save_password(account: &str, password: &str) -> Result<(), String> {
    // 1. Remove any existing entry (both data-protection and legacy login keychain)
    //    so we can set a fresh access control.
    let _ = delete_password(account);
    let _ = delete_password_legacy(account);

    // 2. Try biometric / data-protection keychain first.
    if let Ok(ac) = make_biometric_access_control() {
        let mut query = base_query(account);
        query.push((cf_str!(kSecAttrAccessControl), ac.into_CFType()));
        query.push((cf_str!(kSecValueData), CFData::from_buffer(password.as_bytes()).into_CFType()));

        let dict = CFDictionary::from_CFType_pairs(&query);
        let mut ret = ptr::null();
        let status = unsafe { SecItemAdd(dict.as_concrete_TypeRef(), &mut ret) };

        if status == 0 {
            return Ok(());
        }

        // -34018 = errSecMissingEntitlement: app not signed with keychain-access-groups.
        // This is expected in `tauri dev` (unsigned). Fall through to legacy path.
        if status != -34018 {
            return Err(format!("Keychain SecItemAdd error: OSStatus {status}"));
        }

        tracing::warn!(
            account,
            "data-protection keychain unavailable (errSecMissingEntitlement), \
             falling back to login keychain — run a signed build for Touch ID support"
        );
    }

    // 3. Fallback: save to legacy login keychain (no biometric, no data-protection).
    save_password_legacy(account, password)
}

/// Save to the legacy login keychain (no `kSecUseDataProtectionKeychain`, no access control).
/// Used as a fallback in development / unsigned builds.
fn save_password_legacy(account: &str, password: &str) -> Result<(), String> {
    let query: Vec<(CFString, core_foundation::base::CFType)> = vec![
        (cf_str!(kSecClass), cf_str!(kSecClassGenericPassword).into_CFType()),
        (cf_str!(kSecAttrService), CFString::from(SERVICE).into_CFType()),
        (cf_str!(kSecAttrAccount), CFString::from(account).into_CFType()),
        (cf_str!(kSecValueData), CFData::from_buffer(password.as_bytes()).into_CFType()),
    ];
    let dict = CFDictionary::from_CFType_pairs(&query);
    let mut ret = ptr::null();
    let status = unsafe { SecItemAdd(dict.as_concrete_TypeRef(), &mut ret) };
    if status == 0 {
        Ok(())
    } else {
        Err(format!("Legacy keychain SecItemAdd error: OSStatus {status}"))
    }
}

/// Delete from the legacy login keychain (no `kSecUseDataProtectionKeychain`).
fn delete_password_legacy(account: &str) -> Result<(), String> {
    let query: Vec<(CFString, core_foundation::base::CFType)> = vec![
        (cf_str!(kSecClass), cf_str!(kSecClassGenericPassword).into_CFType()),
        (cf_str!(kSecAttrService), CFString::from(SERVICE).into_CFType()),
        (cf_str!(kSecAttrAccount), CFString::from(account).into_CFType()),
    ];
    let dict = CFDictionary::from_CFType_pairs(&query);
    let status = unsafe { SecItemDelete(dict.as_concrete_TypeRef()) };
    if status == 0 || status == errSecItemNotFound {
        Ok(())
    } else {
        Err(format!("Legacy keychain SecItemDelete error: OSStatus {status}"))
    }
}

/// Retrieve the password for `account`.
///
/// Strategy:
///   1. Try data-protection keychain (new entries with Touch ID access control).
///      macOS will show a Touch ID sheet (or passcode fallback) before returning data.
///   2. If not found, fall back to the legacy login keychain (old entries saved
///      by `set_generic_password` before the biometric upgrade).
///
/// Returns `None` if no entry exists in either keychain.
pub fn get_password(account: &str) -> Result<Option<String>, String> {
    // ── Step 1: try data-protection keychain (Touch ID entries) ──────────────
    if let Some(pw) = get_password_from_data_protection(account)? {
        return Ok(Some(pw));
    }

    // ── Step 2: fallback to legacy login keychain ─────────────────────────────
    // Old entries were saved with `set_generic_password` which uses the login
    // keychain.  We read them here so existing connections still work.
    // The OS may show the old "Enter login keychain password" dialog for these.
    tracing::debug!(account, "data-protection keychain miss, trying legacy login keychain");
    get_password_from_legacy(account)
}

/// Read from the data-protection keychain (new Touch ID–protected entries).
fn get_password_from_data_protection(account: &str) -> Result<Option<String>, String> {
    let mut query = base_query(account); // includes kSecUseDataProtectionKeychain = true
    query.push((cf_str!(kSecReturnData), CFBoolean::true_value().into_CFType()));
    query.push((cf_str!(kSecMatchLimit), CFNumber::from(1i32).into_CFType()));
    // kSecUseAuthenticationUI = "allow" → OS shows Touch ID / passcode sheet.
    query.push((
        cf_str!(kSecUseAuthenticationUI),
        CFString::from("allow").into_CFType(),
    ));

    let dict = CFDictionary::from_CFType_pairs(&query);
    let mut ret: CFTypeRef = ptr::null();
    let status = unsafe { SecItemCopyMatching(dict.as_concrete_TypeRef(), &mut ret) };

    if status == errSecItemNotFound {
        return Ok(None);
    }
    if status != 0 {
        // -25293 = errSecAuthFailed (user cancelled Touch ID / passcode)
        // Treat as "not found" so we don't fall through to legacy and double-prompt.
        if status == -25293 {
            return Err("Authentication cancelled by user".into());
        }
        return Err(format!("Keychain SecItemCopyMatching error: OSStatus {status}"));
    }

    decode_cfdata(ret)
}

/// Read from the legacy login keychain (entries saved before biometric upgrade).
fn get_password_from_legacy(account: &str) -> Result<Option<String>, String> {
    // Build query WITHOUT kSecUseDataProtectionKeychain so it searches the
    // default login keychain where old entries live.
    let query: Vec<(CFString, core_foundation::base::CFType)> = vec![
        (cf_str!(kSecClass), cf_str!(kSecClassGenericPassword).into_CFType()),
        (cf_str!(kSecAttrService), CFString::from(SERVICE).into_CFType()),
        (cf_str!(kSecAttrAccount), CFString::from(account).into_CFType()),
        (cf_str!(kSecReturnData), CFBoolean::true_value().into_CFType()),
        (cf_str!(kSecMatchLimit), CFNumber::from(1i32).into_CFType()),
    ];

    let dict = CFDictionary::from_CFType_pairs(&query);
    let mut ret: CFTypeRef = ptr::null();
    let status = unsafe { SecItemCopyMatching(dict.as_concrete_TypeRef(), &mut ret) };

    if status == errSecItemNotFound {
        return Ok(None);
    }
    if status != 0 {
        return Err(format!("Legacy keychain SecItemCopyMatching error: OSStatus {status}"));
    }

    decode_cfdata(ret)
}

/// Decode a `CFTypeRef` that is expected to be a `CFData` containing UTF-8 bytes.
fn decode_cfdata(ret: CFTypeRef) -> Result<Option<String>, String> {
    if ret.is_null() {
        return Err("Keychain returned null data".into());
    }
    let type_id = unsafe { CFGetTypeID(ret) };
    if type_id != CFData::type_id() {
        unsafe { CFRelease(ret) };
        return Err("Keychain returned unexpected type".into());
    }
    let data = unsafe { CFData::wrap_under_create_rule(ret as CFDataRef) };
    let pw = String::from_utf8(data.bytes().to_vec())
        .map_err(|e| format!("Keychain decode error: {e}"))?;
    Ok(Some(pw))
}

/// Delete the Keychain entry for `account`.  Silently succeeds if not found.
/// Cleans up both data-protection keychain and legacy login keychain entries.
pub fn delete_password(account: &str) -> Result<(), String> {
    let query = base_query(account);
    let dict = CFDictionary::from_CFType_pairs(&query);
    let status = unsafe { SecItemDelete(dict.as_concrete_TypeRef()) };
    if status != 0 && status != errSecItemNotFound {
        return Err(format!("Keychain SecItemDelete error: OSStatus {status}"));
    }
    // Also clean up any legacy login keychain entry.
    let _ = delete_password_legacy(account);
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn biometric_available_does_not_panic() {
        let _ = is_biometric_available();
    }
}
