// Package storage K线数据仓库
package storage

import (
	"context"
	"encoding/json"
	"fmt"
	"time"

	"github.com/shopspring/decimal"

	"github.com/quant/go-market-service/internal/model"
)

// KlineRepository K线数据仓库
type KlineRepository struct {
	*Storage
}

// NewKlineRepository 创建K线仓库
func NewKlineRepository(s *Storage) *KlineRepository {
	return &KlineRepository{Storage: s}
}

// Save 保存K线
func (r *KlineRepository) Save(ctx context.Context, kline *model.Kline) error {
	entity := r.toEntity(kline)
	
	// 使用upsert
	result := r.DB.WithContext(ctx).
		Where("time = ? AND exchange = ? AND symbol = ? AND timeframe = ?",
			entity.Time, entity.Exchange, entity.Symbol, entity.Timeframe).
		Assign(entity).
		FirstOrCreate(entity)

	if result.Error != nil {
		return fmt.Errorf("保存K线失败: %w", result.Error)
	}

	// 更新Redis缓存
	r.updateCache(ctx, kline)

	return nil
}

// SaveBatch 批量保存K线
func (r *KlineRepository) SaveBatch(ctx context.Context, klines []*model.Kline) error {
	if len(klines) == 0 {
		return nil
	}

	entities := make([]*model.KlineEntity, len(klines))
	for i, k := range klines {
		entities[i] = r.toEntity(k)
	}

	// 使用批量插入
	result := r.DB.WithContext(ctx).CreateInBatches(entities, 100)
	if result.Error != nil {
		return fmt.Errorf("批量保存K线失败: %w", result.Error)
	}

	return nil
}

// GetKlines 获取K线数据
func (r *KlineRepository) GetKlines(ctx context.Context, exchange model.Exchange, symbol string, tf model.Timeframe, start, end time.Time, limit int) ([]*model.Kline, error) {
	var entities []model.KlineEntity

	query := r.DB.WithContext(ctx).
		Where("exchange = ? AND symbol = ? AND timeframe = ?", exchange, symbol, tf).
		Where("time >= ? AND time <= ?", start, end).
		Order("time ASC")

	if limit > 0 {
		query = query.Limit(limit)
	}

	if err := query.Find(&entities).Error; err != nil {
		return nil, fmt.Errorf("查询K线失败: %w", err)
	}

	klines := make([]*model.Kline, len(entities))
	for i, e := range entities {
		klines[i] = r.toModel(&e)
	}

	return klines, nil
}

// GetLatestKline 获取最新K线
func (r *KlineRepository) GetLatestKline(ctx context.Context, exchange model.Exchange, symbol string, tf model.Timeframe) (*model.Kline, error) {
	// 先从Redis获取
	cacheKey := r.cacheKey(exchange, symbol, tf)
	data, err := r.Redis.Get(ctx, cacheKey).Bytes()
	if err == nil {
		var kline model.Kline
		if json.Unmarshal(data, &kline) == nil {
			return &kline, nil
		}
	}

	// 从数据库获取
	var entity model.KlineEntity
	result := r.DB.WithContext(ctx).
		Where("exchange = ? AND symbol = ? AND timeframe = ?", exchange, symbol, tf).
		Order("time DESC").
		First(&entity)

	if result.Error != nil {
		return nil, fmt.Errorf("查询最新K线失败: %w", result.Error)
	}

	return r.toModel(&entity), nil
}

// GetKlinesByRange 按时间范围获取K线
func (r *KlineRepository) GetKlinesByRange(ctx context.Context, exchange model.Exchange, symbol string, tf model.Timeframe, start, end time.Time) ([]*model.Kline, error) {
	return r.GetKlines(ctx, exchange, symbol, tf, start, end, 0)
}

// GetRecentKlines 获取最近N根K线
func (r *KlineRepository) GetRecentKlines(ctx context.Context, exchange model.Exchange, symbol string, tf model.Timeframe, count int) ([]*model.Kline, error) {
	var entities []model.KlineEntity

	result := r.DB.WithContext(ctx).
		Where("exchange = ? AND symbol = ? AND timeframe = ?", exchange, symbol, tf).
		Order("time DESC").
		Limit(count).
		Find(&entities)

	if result.Error != nil {
		return nil, fmt.Errorf("查询最近K线失败: %w", result.Error)
	}

	// 反转顺序
	klines := make([]*model.Kline, len(entities))
	for i := len(entities) - 1; i >= 0; i-- {
		klines[len(entities)-1-i] = r.toModel(&entities[i])
	}

	return klines, nil
}

// DeleteOldKlines 删除旧K线
func (r *KlineRepository) DeleteOldKlines(ctx context.Context, retentionDays int) error {
	cutoff := time.Now().AddDate(0, 0, -retentionDays)

	result := r.DB.WithContext(ctx).
		Where("time < ?", cutoff).
		Delete(&model.KlineEntity{})

	if result.Error != nil {
		return fmt.Errorf("删除旧K线失败: %w", result.Error)
	}

	r.log.Info("已删除旧K线",
		zap.Int("retention_days", retentionDays),
		zap.Int64("deleted", result.RowsAffected),
	)

	return nil
}

// toEntity 转换为数据库实体
func (r *KlineRepository) toEntity(k *model.Kline) *model.KlineEntity {
	open, _ := k.Open.Float64()
	high, _ := k.High.Float64()
	low, _ := k.Low.Float64()
	closePrice, _ := k.Close.Float64()
	volume, _ := k.Volume.Float64()
	quoteVolume, _ := k.QuoteVolume.Float64()

	return &model.KlineEntity{
		Time:        k.OpenTime,
		Exchange:    string(k.Exchange),
		Symbol:      k.Symbol,
		Timeframe:   string(k.Timeframe),
		Open:        open,
		High:        high,
		Low:         low,
		Close:       closePrice,
		Volume:      volume,
		QuoteVolume: quoteVolume,
		TradeCount:  k.TradeCount,
	}
}

// toModel 转换为模型
func (r *KlineRepository) toModel(e *model.KlineEntity) *model.Kline {
	return &model.Kline{
		Exchange:    model.Exchange(e.Exchange),
		Symbol:      e.Symbol,
		Timeframe:   model.Timeframe(e.Timeframe),
		OpenTime:    e.Time,
		Open:        decimal.NewFromFloat(e.Open),
		High:        decimal.NewFromFloat(e.High),
		Low:         decimal.NewFromFloat(e.Low),
		Close:       decimal.NewFromFloat(e.Close),
		Volume:      decimal.NewFromFloat(e.Volume),
		QuoteVolume: decimal.NewFromFloat(e.QuoteVolume),
		TradeCount:  e.TradeCount,
		IsClosed:    true,
	}
}

// cacheKey 生成缓存key
func (r *KlineRepository) cacheKey(exchange model.Exchange, symbol string, tf model.Timeframe) string {
	return fmt.Sprintf("kline:%s:%s:%s", exchange, symbol, tf)
}

// updateCache 更新缓存
func (r *KlineRepository) updateCache(ctx context.Context, kline *model.Kline) {
	cacheKey := r.cacheKey(kline.Exchange, kline.Symbol, kline.Timeframe)
	data, _ := json.Marshal(kline)
	r.Redis.Set(ctx, cacheKey, data, 5*time.Minute)
}
