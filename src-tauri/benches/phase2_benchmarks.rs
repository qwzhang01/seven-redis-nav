//! Performance benchmarks for Phase 2 SSH/TLS connection features.
//!
//! Run with: cargo bench --bench phase2_benchmarks
//! (Requires nightly or criterion)

use criterion::{black_box, criterion_group, criterion_main, Criterion};
use seven_redis_nav_lib::models::connection::{
    ConnectionConfig, ConnectionType, SshAuthMethod, SshConfig, TlsConfig,
};
use seven_redis_nav_lib::services::tls_connection::{build_tls_redis_url, validate_tls_config};

// ---- TLS URL generation benchmark ----

fn bench_build_tls_url(c: &mut Criterion) {
    c.bench_function("build_tls_redis_url_no_password", |b| {
        b.iter(|| {
            black_box(build_tls_redis_url(
                black_box("redis.example.com"),
                black_box(6380),
                black_box(None),
            ))
        })
    });

    c.bench_function("build_tls_redis_url_with_password", |b| {
        b.iter(|| {
            black_box(build_tls_redis_url(
                black_box("redis.example.com"),
                black_box(6380),
                black_box(Some("supersecretpassword")),
            ))
        })
    });
}

// ---- TLS config validation benchmark ----

fn bench_validate_tls_config(c: &mut Criterion) {
    let config_empty = TlsConfig::default();
    c.bench_function("validate_tls_config_empty", |b| {
        b.iter(|| {
            black_box(validate_tls_config(black_box(&config_empty)))
        })
    });

    let config_no_verify = TlsConfig {
        verify_cert: false,
        ..Default::default()
    };
    c.bench_function("validate_tls_config_no_verify", |b| {
        b.iter(|| {
            black_box(validate_tls_config(black_box(&config_no_verify)))
        })
    });
}

// ---- ConnectionConfig serialization benchmark ----

fn bench_config_serialization(c: &mut Criterion) {
    let tcp_config = ConnectionConfig {
        id: "bench-tcp".to_string(),
        name: "Benchmark TCP".to_string(),
        group_name: "bench".to_string(),
        host: "127.0.0.1".to_string(),
        port: 6379,
        password: None,
        has_password: false,
        auth_db: 0,
        timeout_ms: 5000,
        sort_order: 0,
        connection_type: ConnectionType::Tcp,
        ssh_config: None,
        tls_config: None,
    };

    let ssh_config = ConnectionConfig {
        id: "bench-ssh".to_string(),
        name: "Benchmark SSH".to_string(),
        group_name: "bench".to_string(),
        host: "10.0.0.1".to_string(),
        port: 6379,
        password: None,
        has_password: false,
        auth_db: 0,
        timeout_ms: 5000,
        sort_order: 0,
        connection_type: ConnectionType::Ssh,
        ssh_config: Some(SshConfig {
            host: "jump.example.com".to_string(),
            port: 22,
            username: "ubuntu".to_string(),
            auth_method: SshAuthMethod::Password,
            password: Some("secret".to_string()),
            private_key_path: None,
            private_key_passphrase: None,
            timeout_ms: 10000,
        }),
        tls_config: None,
    };

    let tls_config = ConnectionConfig {
        id: "bench-tls".to_string(),
        name: "Benchmark TLS".to_string(),
        group_name: "bench".to_string(),
        host: "redis.example.com".to_string(),
        port: 6380,
        password: Some("tlspass".to_string()),
        has_password: true,
        auth_db: 0,
        timeout_ms: 5000,
        sort_order: 0,
        connection_type: ConnectionType::Tls,
        ssh_config: None,
        tls_config: Some(TlsConfig {
            verify_cert: true,
            ca_cert_path: Some("/etc/ssl/ca.pem".to_string()),
            client_cert_path: None,
            client_key_path: None,
            min_tls_version: Some("tls1.2".to_string()),
            server_name: Some("redis.internal".to_string()),
        }),
    };

    c.bench_function("serialize_tcp_config", |b| {
        b.iter(|| black_box(serde_json::to_string(black_box(&tcp_config)).unwrap()))
    });

    c.bench_function("serialize_ssh_config", |b| {
        b.iter(|| black_box(serde_json::to_string(black_box(&ssh_config)).unwrap()))
    });

    c.bench_function("serialize_tls_config", |b| {
        b.iter(|| black_box(serde_json::to_string(black_box(&tls_config)).unwrap()))
    });

    // Deserialization benchmarks
    let tcp_json = serde_json::to_string(&tcp_config).unwrap();
    let ssh_json = serde_json::to_string(&ssh_config).unwrap();
    let tls_json = serde_json::to_string(&tls_config).unwrap();

    c.bench_function("deserialize_tcp_config", |b| {
        b.iter(|| {
            black_box(serde_json::from_str::<ConnectionConfig>(black_box(&tcp_json)).unwrap())
        })
    });

    c.bench_function("deserialize_ssh_config", |b| {
        b.iter(|| {
            black_box(serde_json::from_str::<ConnectionConfig>(black_box(&ssh_json)).unwrap())
        })
    });

    c.bench_function("deserialize_tls_config", |b| {
        b.iter(|| {
            black_box(serde_json::from_str::<ConnectionConfig>(black_box(&tls_json)).unwrap())
        })
    });
}

criterion_group!(
    benches,
    bench_build_tls_url,
    bench_validate_tls_config,
    bench_config_serialization,
);
criterion_main!(benches);
