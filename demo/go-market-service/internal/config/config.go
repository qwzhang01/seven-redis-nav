// Package config 配置管理
package config

import (
	"fmt"
	"strings"

	"github.com/spf13/viper"
)

// Config 系统配置
type Config struct {
	Env     string        `mapstructure:"env"`     // 环境: dev, test, production
	Server  ServerConfig  `mapstructure:"server"`  // HTTP服务配置
	Storage StorageConfig `mapstructure:"storage"` // 存储配置
	Log     LogConfig     `mapstructure:"log"`     // 日志配置
	Market  MarketConfig  `mapstructure:"market"`  // 行情配置
	Kafka   KafkaConfig   `mapstructure:"kafka"`   // Kafka配置
	GRPC    GRPCConfig    `mapstructure:"grpc"`    // gRPC配置
}

// ServerConfig HTTP服务配置
type ServerConfig struct {
	Addr         string `mapstructure:"addr"`          // 监听地址
	ReadTimeout  int    `mapstructure:"read_timeout"`  // 读取超时(秒)
	WriteTimeout int    `mapstructure:"write_timeout"` // 写入超时(秒)
}

// StorageConfig 存储配置
type StorageConfig struct {
	// PostgreSQL/TimescaleDB
	Postgres PostgresConfig `mapstructure:"postgres"`
	// Redis
	Redis RedisConfig `mapstructure:"redis"`
}

// PostgresConfig PostgreSQL配置
type PostgresConfig struct {
	Host     string `mapstructure:"host"`
	Port     int    `mapstructure:"port"`
	User     string `mapstructure:"user"`
	Password string `mapstructure:"password"`
	DBName   string `mapstructure:"dbname"`
	SSLMode  string `mapstructure:"sslmode"`
	MaxConns int    `mapstructure:"max_conns"`
}

// DSN 返回数据库连接字符串
func (c *PostgresConfig) DSN() string {
	return fmt.Sprintf(
		"host=%s port=%d user=%s password=%s dbname=%s sslmode=%s",
		c.Host, c.Port, c.User, c.Password, c.DBName, c.SSLMode,
	)
}

// RedisConfig Redis配置
type RedisConfig struct {
	Addr     string `mapstructure:"addr"`
	Password string `mapstructure:"password"`
	DB       int    `mapstructure:"db"`
	PoolSize int    `mapstructure:"pool_size"`
}

// LogConfig 日志配置
type LogConfig struct {
	Level      string `mapstructure:"level"`       // 日志级别: debug, info, warn, error
	Format     string `mapstructure:"format"`      // 格式: json, console
	OutputPath string `mapstructure:"output_path"` // 输出路径
}

// MarketConfig 行情配置
type MarketConfig struct {
	// 交易所配置
	Exchanges []ExchangeConfig `mapstructure:"exchanges"`
	// K线周期
	Timeframes []string `mapstructure:"timeframes"`
	// 数据保留天数
	RetentionDays int `mapstructure:"retention_days"`
}

// ExchangeConfig 交易所配置
type ExchangeConfig struct {
	Name      string   `mapstructure:"name"`       // 交易所名称: binance, okx, bybit
	Enabled   bool     `mapstructure:"enabled"`    // 是否启用
	APIKey    string   `mapstructure:"api_key"`    // API Key
	SecretKey string   `mapstructure:"secret_key"` // Secret Key
	Symbols   []string `mapstructure:"symbols"`    // 交易对列表
	// WebSocket配置
	WSEndpoint string `mapstructure:"ws_endpoint"` // WebSocket地址
	// REST配置
	RESTEndpoint string `mapstructure:"rest_endpoint"` // REST API地址
	RateLimit    int    `mapstructure:"rate_limit"`    // 每秒请求限制
}

// KafkaConfig Kafka配置
type KafkaConfig struct {
	Brokers       []string `mapstructure:"brokers"`
	TopicTick     string   `mapstructure:"topic_tick"`     // Tick数据主题
	TopicKline    string   `mapstructure:"topic_kline"`    // K线数据主题
	TopicSignal   string   `mapstructure:"topic_signal"`   // 信号主题
	ConsumerGroup string   `mapstructure:"consumer_group"` // 消费者组
}

// GRPCConfig gRPC配置
type GRPCConfig struct {
	Addr string `mapstructure:"addr"` // gRPC监听地址
}

// Load 加载配置文件
func Load(configPath string) (*Config, error) {
	v := viper.New()

	// 设置配置文件
	v.SetConfigFile(configPath)

	// 环境变量支持
	v.SetEnvPrefix("MARKET")
	v.SetEnvKeyReplacer(strings.NewReplacer(".", "_"))
	v.AutomaticEnv()

	// 读取配置
	if err := v.ReadInConfig(); err != nil {
		return nil, fmt.Errorf("读取配置文件失败: %w", err)
	}

	var cfg Config
	if err := v.Unmarshal(&cfg); err != nil {
		return nil, fmt.Errorf("解析配置失败: %w", err)
	}

	// 设置默认值
	setDefaults(&cfg)

	return &cfg, nil
}

// setDefaults 设置默认值
func setDefaults(cfg *Config) {
	if cfg.Env == "" {
		cfg.Env = "dev"
	}
	if cfg.Server.Addr == "" {
		cfg.Server.Addr = ":8080"
	}
	if cfg.Server.ReadTimeout == 0 {
		cfg.Server.ReadTimeout = 30
	}
	if cfg.Server.WriteTimeout == 0 {
		cfg.Server.WriteTimeout = 30
	}
	if cfg.Log.Level == "" {
		cfg.Log.Level = "info"
	}
	if cfg.Log.Format == "" {
		cfg.Log.Format = "json"
	}
	if len(cfg.Market.Timeframes) == 0 {
		cfg.Market.Timeframes = []string{"1m", "5m", "15m", "30m", "1h", "4h", "1d"}
	}
	if cfg.Market.RetentionDays == 0 {
		cfg.Market.RetentionDays = 365
	}
}
