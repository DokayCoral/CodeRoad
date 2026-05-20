package service

import (
	"errors"

	"cdd/src/internal/model"
	"cdd/src/internal/repo"
	"cdd/src/pkg/mq"
)

// validTransitions defines the allowed status transitions.
var validTransitions = map[int][]int{
	model.RideStatusPending:  {model.RideStatusMatched, model.RideStatusCancelled},
	model.RideStatusMatched:  {model.RideStatusAccepted, model.RideStatusCancelled},
	model.RideStatusAccepted: {model.RideStatusArrived},
	model.RideStatusArrived:  {model.RideStatusStarted},
	model.RideStatusStarted:  {model.RideStatusCompleted},
}

type LifecycleService struct {
	rideRepo *repo.RideRepo
	pricing  *PricingService
	mqClient *mq.Client
}

func NewLifecycleService(rideRepo *repo.RideRepo, pricing *PricingService, mqClient *mq.Client) *LifecycleService {
	return &LifecycleService{
		rideRepo: rideRepo,
		pricing:  pricing,
		mqClient: mqClient,
	}
}

func (s *LifecycleService) Accept(rideID int64, driverID string) error {
	ride, err := s.rideRepo.GetRideByID(rideID)
	if err != nil || ride == nil {
		return errors.New("ride not found")
	}
	if !s.canTransition(ride.Status, model.RideStatusAccepted) {
		return errors.New("ride cannot be accepted in current status")
	}
	if ride.DriverID != driverID {
		return errors.New("driver not assigned to this ride")
	}

	ride.Status = model.RideStatusAccepted
	if err := s.rideRepo.UpdateRideStatus(rideID, model.RideStatusMatched, ride); err != nil {
		return err
	}
	s.publishEvent(rideID, model.RideStatusAccepted, driverID)
	return nil
}

func (s *LifecycleService) Arrive(rideID int64, driverID string) error {
	ride, err := s.rideRepo.GetRideByID(rideID)
	if err != nil || ride == nil {
		return errors.New("ride not found")
	}
	if !s.canTransition(ride.Status, model.RideStatusArrived) {
		return errors.New("ride cannot arrive in current status")
	}
	if ride.DriverID != driverID {
		return errors.New("driver not assigned to this ride")
	}

	ride.Status = model.RideStatusArrived
	if err := s.rideRepo.UpdateRideStatus(rideID, model.RideStatusAccepted, ride); err != nil {
		return err
	}
	s.publishEvent(rideID, model.RideStatusArrived, driverID)
	return nil
}

func (s *LifecycleService) Start(rideID int64, driverID string) error {
	ride, err := s.rideRepo.GetRideByID(rideID)
	if err != nil || ride == nil {
		return errors.New("ride not found")
	}
	if !s.canTransition(ride.Status, model.RideStatusStarted) {
		return errors.New("ride cannot start in current status")
	}
	if ride.DriverID != driverID {
		return errors.New("driver not assigned to this ride")
	}

	ride.Status = model.RideStatusStarted
	if err := s.rideRepo.UpdateRideStatus(rideID, model.RideStatusArrived, ride); err != nil {
		return err
	}
	s.publishEvent(rideID, model.RideStatusStarted, driverID)
	return nil
}

func (s *LifecycleService) Complete(rideID int64, driverID string, actualDistance, actualDuration int) error {
	ride, err := s.rideRepo.GetRideByID(rideID)
	if err != nil || ride == nil {
		return errors.New("ride not found")
	}
	if !s.canTransition(ride.Status, model.RideStatusCompleted) {
		return errors.New("ride cannot complete in current status")
	}
	if ride.DriverID != driverID {
		return errors.New("driver not assigned to this ride")
	}

	finalPrice := s.pricing.CalculatePrice(actualDistance, actualDuration)
	ride.Status = model.RideStatusCompleted
	ride.Price = finalPrice
	ride.Distance = actualDistance
	ride.Duration = actualDuration

	if err := s.rideRepo.UpdateRideStatus(rideID, model.RideStatusStarted, ride); err != nil {
		return err
	}
	s.publishEvent(rideID, model.RideStatusCompleted, driverID)
	return nil
}

func (s *LifecycleService) Cancel(rideID int64, cancelledBy, reason string) error {
	ride, err := s.rideRepo.GetRideByID(rideID)
	if err != nil || ride == nil {
		return errors.New("ride not found")
	}
	if !s.canTransition(ride.Status, model.RideStatusCancelled) {
		return errors.New("ride cannot be cancelled in current status")
	}

	oldStatus := ride.Status
	ride.Status = model.RideStatusCancelled
	ride.CancelBy = cancelledBy
	ride.CancelReason = reason

	if err := s.rideRepo.UpdateRideStatus(rideID, oldStatus, ride); err != nil {
		return err
	}
	s.publishEvent(rideID, model.RideStatusCancelled, ride.DriverID)
	return nil
}

func (s *LifecycleService) canTransition(from, to int) bool {
	allowed, ok := validTransitions[from]
	if !ok {
		return false
	}
	for _, t := range allowed {
		if t == to {
			return true
		}
	}
	return false
}

func (s *LifecycleService) publishEvent(rideID int64, status int, driverID string) {
	_ = s.mqClient.Publish(mq.RideEventQueue, map[string]interface{}{
		"ride_id":   rideID,
		"status":    status,
		"driver_id": driverID,
	})
}
