package service

import (
	"context"
	"encoding/json"
	"log"

	"cdd/src/internal/model"
	"cdd/src/internal/repo"
	"cdd/src/pkg/mq"

	amqp "github.com/rabbitmq/amqp091-go"
)

const defaultMatchRadius = 3.0 // km

type MatchingService struct {
	rideRepo          *repo.RideRepo
	driverRepo        *repo.DriverRepo
	driverLocationRepo *repo.DriverLocationRepo
	mqClient          *mq.Client
}

func NewMatchingService(
	rideRepo *repo.RideRepo,
	driverRepo *repo.DriverRepo,
	driverLocationRepo *repo.DriverLocationRepo,
	mqClient *mq.Client,
) *MatchingService {
	return &MatchingService{
		rideRepo:           rideRepo,
		driverRepo:         driverRepo,
		driverLocationRepo: driverLocationRepo,
		mqClient:           mqClient,
	}
}

type rideRequestMsg struct {
	RideID      int64   `json:"ride_id"`
	OriginLng   float64 `json:"origin_lng"`
	OriginLat   float64 `json:"origin_lat"`
	PassengerID string  `json:"passenger_id"`
}

// Start begins consuming ride request messages from RabbitMQ.
func (s *MatchingService) Start(ctx context.Context) error {
	if err := s.mqClient.DeclareQueue(mq.RideRequestQueue); err != nil {
		return err
	}
	if err := s.mqClient.DeclareQueue(mq.RideEventQueue); err != nil {
		return err
	}

	msgs, err := s.mqClient.Consume(mq.RideRequestQueue)
	if err != nil {
		return err
	}

	go func() {
		for {
			select {
			case <-ctx.Done():
				return
			case msg, ok := <-msgs:
				if !ok {
					return
				}
				s.handleMatch(ctx, msg)
			}
		}
	}()

	log.Println("matching service started")
	return nil
}

func (s *MatchingService) handleMatch(ctx context.Context, msg amqp.Delivery) {
	var req rideRequestMsg
	if err := json.Unmarshal(msg.Body, &req); err != nil {
		log.Printf("failed to unmarshal match request: %v", err)
		msg.Nack(false, false)
		return
	}

	ride, err := s.rideRepo.GetRideByID(req.RideID)
	if err != nil || ride == nil {
		log.Printf("ride %d not found", req.RideID)
		msg.Nack(false, false)
		return
	}
	if ride.Status != model.RideStatusPending {
		msg.Ack(false) // already processed
		return
	}

	// Search nearby drivers
	drivers, err := s.driverLocationRepo.SearchNearbyDrivers(ctx, req.OriginLng, req.OriginLat, defaultMatchRadius)
	if err != nil || len(drivers) == 0 {
		log.Printf("no nearby drivers for ride %d", req.RideID)
		msg.Ack(false) // ack and let the ride stay pending (could be retried)
		return
	}

	// Try to match the nearest available driver
	for _, d := range drivers {
		// Try lock
		locked, err := s.driverLocationRepo.TryLockMatch(ctx, d.Name)
		if err != nil || !locked {
			continue
		}

		// Verify driver status
		driver, err := s.driverRepo.GetDriverByID(d.Name)
		if err != nil || driver == nil || driver.Status != model.DriverStatusOnline {
			s.driverLocationRepo.UnlockMatch(ctx, d.Name)
			continue
		}

		// Update ride status to Matched
		ride.Status = model.RideStatusMatched
		ride.DriverID = driver.ID
		if err := s.rideRepo.UpdateRideStatus(ride.ID, model.RideStatusPending, ride); err != nil {
			log.Printf("failed to update ride %d status: %v", ride.ID, err)
			s.driverLocationRepo.UnlockMatch(ctx, d.Name)
			continue
		}

		// Update driver status to Busy
		_ = s.driverRepo.UpdateDriverStatus(driver.ID, model.DriverStatusBusy)

		// Publish ride event
		s.mqClient.Publish(mq.RideEventQueue, map[string]interface{}{
			"ride_id":   ride.ID,
			"status":    ride.Status,
			"driver_id": driver.ID,
		})

		log.Printf("ride %d matched to driver %s", ride.ID, driver.ID)
		msg.Ack(false)
		return
	}

	// No driver available, leave ride pending
	msg.Ack(false)
}
