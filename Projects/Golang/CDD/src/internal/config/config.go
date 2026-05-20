package config

import (
	"os"
	"strconv"
)

type Config struct {
	DB       DBConfig
	Redis    RedisConfig
	RabbitMQ RabbitMQConfig
	Pricing  PricingConfig
}

type DBConfig struct {
	DSN string
}

type RedisConfig struct {
	Addr     string
	Password string
	DB       int
}

type RabbitMQConfig struct {
	URL string
}

type PricingConfig struct {
	BasePrice      int // 起步价（分）
	BaseDistance   int // 起步里程（米）
	BaseDuration   int // 起步时长（秒）
	DistanceRate   int // 里程费率（分/公里）
	TimeRate       int // 时长费率（分/分钟）
	MinPrice       int // 最低消费（分）
}

func Load() *Config {
	return &Config{
		DB: DBConfig{
			DSN: getEnv("DB_DSN", "root:root@tcp(127.0.0.1:3306)/cdd?charset=utf8mb4&parseTime=True&loc=Local"),
		},
		Redis: RedisConfig{
			Addr:     getEnv("REDIS_ADDR", "127.0.0.1:6379"),
			Password: getEnv("REDIS_PASSWORD", ""),
			DB:       getEnvInt("REDIS_DB", 0),
		},
		RabbitMQ: RabbitMQConfig{
			URL: getEnv("RABBITMQ_URL", "amqp://guest:guest@127.0.0.1:5672/"),
		},
		Pricing: PricingConfig{
			BasePrice:    getEnvInt("PRICING_BASE_PRICE", 1000),
			BaseDistance: getEnvInt("PRICING_BASE_DISTANCE", 3000),
			BaseDuration: getEnvInt("PRICING_BASE_DURATION", 600),
			DistanceRate: getEnvInt("PRICING_DISTANCE_RATE", 200),
			TimeRate:     getEnvInt("PRICING_TIME_RATE", 30),
			MinPrice:     getEnvInt("PRICING_MIN_PRICE", 1000),
		},
	}
}

func getEnv(key, defaultVal string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return defaultVal
}

func getEnvInt(key string, defaultVal int) int {
	if v := os.Getenv(key); v != "" {
		if iv, err := strconv.Atoi(v); err == nil {
			return iv
		}
	}
	return defaultVal
}
