package service

import (
	"math"

	"cdd/src/internal/config"
)

type PricingService struct {
	cfg config.PricingConfig
}

func NewPricingService(cfg config.PricingConfig) *PricingService {
	return &PricingService{cfg: cfg}
}

// EstimatePrice calculates the estimated fare based on distance (meters) and duration (seconds).
func (s *PricingService) EstimatePrice(distanceM, durationS int) int {
	return s.calculate(distanceM, durationS)
}

// CalculatePrice calculates the final fare. Same formula as estimate for now.
func (s *PricingService) CalculatePrice(distanceM, durationS int) int {
	return s.calculate(distanceM, durationS)
}

func (s *PricingService) calculate(distanceM, durationS int) int {
	price := s.cfg.BasePrice

	// Distance fee: per km beyond base distance
	if distanceM > s.cfg.BaseDistance {
		extraDistKM := float64(distanceM-s.cfg.BaseDistance) / 1000.0
		price += int(math.Ceil(extraDistKM * float64(s.cfg.DistanceRate)))
	}

	// Time fee: per minute beyond base duration
	if durationS > s.cfg.BaseDuration {
		extraTimeMin := float64(durationS-s.cfg.BaseDuration) / 60.0
		price += int(math.Ceil(extraTimeMin * float64(s.cfg.TimeRate)))
	}

	if price < s.cfg.MinPrice {
		price = s.cfg.MinPrice
	}

	return price
}
