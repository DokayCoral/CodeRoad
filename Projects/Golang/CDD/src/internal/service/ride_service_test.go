package service

import (
	"testing"
)

func TestHaversine(t *testing.T) {
	// Tiananmen to Wangfujing: ~1.6km
	d := haversine(116.397428, 39.909204, 116.410585, 39.914457)
	if d < 1000 || d > 2000 {
		t.Errorf("Tiananmen→Wangfujing: expected ~1600m, got %d", d)
	}
}

func TestHaversine_SamePoint(t *testing.T) {
	d := haversine(116.397428, 39.909204, 116.397428, 39.909204)
	if d != 0 {
		t.Errorf("same point: expected 0, got %d", d)
	}
}

func TestHaversine_LongDistance(t *testing.T) {
	// Beijing → Shanghai: ~1068km
	d := haversine(116.4074, 39.9042, 121.4737, 31.2304)
	if d < 900000 || d > 1200000 {
		t.Errorf("Beijing→Shanghai: expected ~1068km, got %dm", d)
	}
}

func TestEstimateDuration(t *testing.T) {
	// 8333m at 30km/h → ~1000 seconds
	dur := estimateDuration(8333)
	if dur < 900 || dur > 1100 {
		t.Errorf("8333m: expected ~1000s, got %d", dur)
	}
}

func TestHaversineAndDuration_Integration(t *testing.T) {
	// Short trip: ~1km
	distance := haversine(116.397, 39.909, 116.405, 39.913)
	duration := estimateDuration(distance)

	if distance <= 0 {
		t.Error("distance should be positive")
	}
	if duration <= 0 {
		t.Error("duration should be positive")
	}

	// Distance should be reasonable (roughly proportional to coordinate change)
	if distance > 5000 {
		t.Errorf("distance too large for short trip: %d", distance)
	}
}
