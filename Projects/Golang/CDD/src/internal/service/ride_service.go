package service

import (
	"context"
	"errors"
	"math"

	"cdd/src/internal/model"
	"cdd/src/internal/repo"
	"cdd/src/pkg/mq"
)

type RideRequest struct {
	PassengerID string  `json:"passenger_id"`
	OriginLng   float64 `json:"origin_lng"`
	OriginLat   float64 `json:"origin_lat"`
	DestLng     float64 `json:"dest_lng"`
	DestLat     float64 `json:"dest_lat"`
}

type RideService struct {
	rideRepo  *repo.RideRepo
	pricing   *PricingService
	mqClient  *mq.Client
}

func NewRideService(rideRepo *repo.RideRepo, pricing *PricingService, mqClient *mq.Client) *RideService {
	return &RideService{
		rideRepo: rideRepo,
		pricing:  pricing,
		mqClient: mqClient,
	}
}

func (s *RideService) HandleRideRequest(ctx context.Context, req RideRequest) (*model.Ride, error) {
	// Check passenger has no active ride
	active, err := s.rideRepo.GetActiveRideByPassenger(req.PassengerID)
	if err != nil {
		return nil, err
	}
	if active != nil {
		return nil, errors.New("passenger already has an active ride")
	}

	// Estimate distance and duration using straight-line distance
	distance := haversine(req.OriginLng, req.OriginLat, req.DestLng, req.DestLat)
	duration := estimateDuration(distance)

	// Calculate estimated price
	price := s.pricing.EstimatePrice(distance, duration)

	ride := &model.Ride{
		PassengerID: req.PassengerID,
		OriginLng:   req.OriginLng,
		OriginLat:   req.OriginLat,
		DestLng:     req.DestLng,
		DestLat:     req.DestLat,
		Status:      model.RideStatusPending,
		Distance:    distance,
		Duration:    duration,
		Price:       price,
	}

	if err := s.rideRepo.CreateRide(ride); err != nil {
		return nil, err
	}

	// Publish to matching queue (fire and forget)
	_ = s.mqClient.Publish(mq.RideRequestQueue, map[string]interface{}{
		"ride_id":       ride.ID,
		"origin_lng":    ride.OriginLng,
		"origin_lat":    ride.OriginLat,
		"passenger_id":  ride.PassengerID,
	})

	return ride, nil
}

// haversine calculates the straight-line distance in meters between two GCJ-02 coordinates.
func haversine(lng1, lat1, lng2, lat2 float64) int {
	const earthRadius = 6371000.0 // meters
	dLat := (lat2 - lat1) * (math.Pi / 180.0)
	dLng := (lng2 - lng1) * (math.Pi / 180.0)
	a := math.Sin(dLat/2)*math.Sin(dLat/2) +
		math.Cos(lat1*(math.Pi/180.0))*math.Cos(lat2*(math.Pi/180.0))*
			math.Sin(dLng/2)*math.Sin(dLng/2)
	c := 2 * math.Atan2(math.Sqrt(a), math.Sqrt(1-a))
	return int(earthRadius * c)
}

// estimateDuration estimates duration in seconds based on distance.
// Assumes average speed of 30 km/h in city.
func estimateDuration(distanceM int) int {
	return int(float64(distanceM) / 8.33) // 30 km/h ≈ 8.33 m/s
}
