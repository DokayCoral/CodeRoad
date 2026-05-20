package service

import (
	"testing"

	"cdd/src/internal/config"
)

func TestEstimatePrice_ShortTrip(t *testing.T) {
	svc := NewPricingService(config.PricingConfig{
		BasePrice:    1000,
		BaseDistance: 3000,
		BaseDuration: 600,
		DistanceRate: 200,
		TimeRate:     30,
		MinPrice:     1000,
	})

	// Within base range: 2.5km, 8min
	price := svc.EstimatePrice(2500, 480)
	if price != 1000 {
		t.Errorf("short trip: expected 1000, got %d", price)
	}
}

func TestEstimatePrice_OverDistance(t *testing.T) {
	svc := NewPricingService(config.PricingConfig{
		BasePrice:    1000,
		BaseDistance: 3000,
		BaseDuration: 600,
		DistanceRate: 200,
		TimeRate:     30,
		MinPrice:     1000,
	})

	// 5km, 12min: 1000 + (5-3)*200 + (12-10)*30 = 1000 + 400 + 60 = 1460
	price := svc.EstimatePrice(5000, 720)
	if price != 1460 {
		t.Errorf("over distance: expected 1460, got %d", price)
	}
}

func TestEstimatePrice_BelowMinPrice(t *testing.T) {
	svc := NewPricingService(config.PricingConfig{
		BasePrice:    1000,
		BaseDistance: 3000,
		BaseDuration: 600,
		DistanceRate: 50,
		TimeRate:     10,
		MinPrice:     1000,
	})

	// Very short: 500m, 2min → calculated < min_price → should be min_price
	price := svc.EstimatePrice(500, 120)
	if price != 1000 {
		t.Errorf("below min: expected 1000, got %d", price)
	}
}

func TestEstimatePrice_LongTrip(t *testing.T) {
	svc := NewPricingService(config.PricingConfig{
		BasePrice:    1000,
		BaseDistance: 3000,
		BaseDuration: 600,
		DistanceRate: 200,
		TimeRate:     30,
		MinPrice:     1000,
	})

	// 10km, 30min: 1000 + 7*200 + 20*30 = 1000 + 1400 + 600 = 3000
	price := svc.EstimatePrice(10000, 1800)
	if price != 3000 {
		t.Errorf("long trip: expected 3000, got %d", price)
	}
}

func TestCalculatePrice_SameAsEstimate(t *testing.T) {
	svc := NewPricingService(config.PricingConfig{
		BasePrice:    1000,
		BaseDistance: 3000,
		BaseDuration: 600,
		DistanceRate: 200,
		TimeRate:     30,
		MinPrice:     1000,
	})

	est := svc.EstimatePrice(5000, 720)
	calc := svc.CalculatePrice(5000, 720)
	if est != calc {
		t.Errorf("estimate (%d) and calculate (%d) should match", est, calc)
	}
}
