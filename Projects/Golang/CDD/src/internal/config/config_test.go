package config

import (
	"os"
	"testing"
)

func TestLoadDefaults(t *testing.T) {
	cfg := Load()

	if cfg.DB.DSN == "" {
		t.Error("DB DSN should have a default")
	}
	if cfg.Redis.Addr == "" {
		t.Error("Redis Addr should have a default")
	}
	if cfg.RabbitMQ.URL == "" {
		t.Error("RabbitMQ URL should have a default")
	}
	if cfg.Pricing.BasePrice != 1000 {
		t.Errorf("BasePrice: expected 1000, got %d", cfg.Pricing.BasePrice)
	}
	if cfg.Pricing.BaseDistance != 3000 {
		t.Errorf("BaseDistance: expected 3000, got %d", cfg.Pricing.BaseDistance)
	}
	if cfg.Pricing.BaseDuration != 600 {
		t.Errorf("BaseDuration: expected 600, got %d", cfg.Pricing.BaseDuration)
	}
	if cfg.Pricing.DistanceRate != 200 {
		t.Errorf("DistanceRate: expected 200, got %d", cfg.Pricing.DistanceRate)
	}
	if cfg.Pricing.TimeRate != 30 {
		t.Errorf("TimeRate: expected 30, got %d", cfg.Pricing.TimeRate)
	}
	if cfg.Pricing.MinPrice != 1000 {
		t.Errorf("MinPrice: expected 1000, got %d", cfg.Pricing.MinPrice)
	}
}

func TestLoadFromEnv(t *testing.T) {
	os.Setenv("DB_DSN", "test:test@tcp(localhost)/test")
	os.Setenv("PRICING_BASE_PRICE", "800")
	defer func() {
		os.Unsetenv("DB_DSN")
		os.Unsetenv("PRICING_BASE_PRICE")
	}()

	cfg := Load()

	if cfg.DB.DSN != "test:test@tcp(localhost)/test" {
		t.Errorf("DB DSN from env: got %s", cfg.DB.DSN)
	}
	if cfg.Pricing.BasePrice != 800 {
		t.Errorf("BasePrice from env: expected 800, got %d", cfg.Pricing.BasePrice)
	}
}

func TestGetEnvInt_Invalid(t *testing.T) {
	os.Setenv("TEST_INVALID_INT", "abc")
	defer os.Unsetenv("TEST_INVALID_INT")

	v := getEnvInt("TEST_INVALID_INT", 42)
	if v != 42 {
		t.Errorf("expected default 42 for invalid int, got %d", v)
	}
}
