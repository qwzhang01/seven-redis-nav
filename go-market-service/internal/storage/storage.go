// Package storage 存储层
package storage

import (
	"context"
	"fmt"
	"time"

	"github.com/redis/go-redis/v9"
	"go.uber.org/zap"
	"gorm.io/driver/postgres"
	"gorm.io/gorm"
	"gorm.io/gorm/logger"

	"github.com/quant/go-market-service/internal/config"
	"github.com/quant/go-market-service/internal/model"
)

// Storage 存储层
type Storage struct {
	DB    *gorm.DB
	Redis *redis.Client
	log   *zap.Logger
}

// New 创建存储层
func New(cfg config.StorageConfig, log *zap.Logger) (*Storage, error) {
	// 连接PostgreSQL
	gormLogger := logger.Default.LogMode(logger.Silent)
	db, err := gorm.Open(postgres.Open(cfg.Postgres.DSN()), &gorm.Config{
		Logger: gormLogger,
	})
	if err != nil {
		return nil, fmt.Errorf("连接数据库失败: %w", err)
	}

	// 配置连接池
	sqlDB, err := db.DB()
	if err != nil {
		return nil, fmt.Errorf("获取数据库连接池失败: %w", err)
	}

	sqlDB.SetMaxOpenConns(cfg.Postgres.MaxConns)
	sqlDB.SetMaxIdleConns(cfg.Postgres.MaxConns / 2)
	sqlDB.SetConnMaxLifetime(time.Hour)

	// 自动迁移
	if err := autoMigrate(db); err != nil {
		return nil, fmt.Errorf("数据库迁移失败: %w", err)
	}

	// 连接Redis
	rdb := redis.NewClient(&redis.Options{
		Addr:     cfg.Redis.Addr,
		Password: cfg.Redis.Password,
		DB:       cfg.Redis.DB,
		PoolSize: cfg.Redis.PoolSize,
	})

	// 测试Redis连接
	ctx := context.Background()
	if err := rdb.Ping(ctx).Err(); err != nil {
		return nil, fmt.Errorf("连接Redis失败: %w", err)
	}

	log.Info("存储层初始化成功")

	return &Storage{
		DB:    db,
		Redis: rdb,
		log:   log.With(zap.String("component", "storage")),
	}, nil
}

// autoMigrate 自动迁移
func autoMigrate(db *gorm.DB) error {
	// 创建TimescaleDB扩展
	db.Exec("CREATE EXTENSION IF NOT EXISTS timescaledb")

	// 迁移表结构
	if err := db.AutoMigrate(
		&model.KlineEntity{},
		&model.TickEntity{},
		&model.IndicatorEntity{},
		&model.SymbolInfo{},
	); err != nil {
		return err
	}

	// 创建超表
	db.Exec(`SELECT create_hypertable('klines', 'time', if_not_exists => TRUE)`)
	db.Exec(`SELECT create_hypertable('ticks', 'time', if_not_exists => TRUE)`)
	db.Exec(`SELECT create_hypertable('indicators', 'time', if_not_exists => TRUE)`)

	return nil
}

// Close 关闭存储层
func (s *Storage) Close() error {
	if s.Redis != nil {
		if err := s.Redis.Close(); err != nil {
			s.log.Error("关闭Redis连接失败", zap.Error(err))
		}
	}

	if s.DB != nil {
		sqlDB, err := s.DB.DB()
		if err == nil {
			if err := sqlDB.Close(); err != nil {
				s.log.Error("关闭数据库连接失败", zap.Error(err))
			}
		}
	}

	s.log.Info("存储层已关闭")
	return nil
}
