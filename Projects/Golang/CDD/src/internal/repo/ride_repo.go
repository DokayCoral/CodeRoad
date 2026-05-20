package repo

import (
	"errors"

	"cdd/src/internal/model"

	"gorm.io/gorm"
	"gorm.io/gorm/clause"
)

type RideRepo struct {
	db *gorm.DB
}

func NewRideRepo(db *gorm.DB) *RideRepo {
	return &RideRepo{db: db}
}

func (r *RideRepo) CreateRide(ride *model.Ride) error {
	return r.db.Create(ride).Error
}

func (r *RideRepo) GetRideByID(id int64) (*model.Ride, error) {
	var ride model.Ride
	if err := r.db.First(&ride, id).Error; err != nil {
		if errors.Is(err, gorm.ErrRecordNotFound) {
			return nil, nil
		}
		return nil, err
	}
	return &ride, nil
}

func (r *RideRepo) UpdateRideStatus(id int64, oldStatus int, ride *model.Ride) error {
	result := r.db.Model(&model.Ride{}).
		Where("id = ? AND status = ?", id, oldStatus).
		Updates(map[string]interface{}{
			"status":    ride.Status,
			"driver_id": ride.DriverID,
			"distance":  ride.Distance,
			"duration":  ride.Duration,
			"price":     ride.Price,
			"cancel_by": ride.CancelBy,
			"cancel_reason": ride.CancelReason,
			"version":   gorm.Expr("version + 1"),
		})
	if result.Error != nil {
		return result.Error
	}
	if result.RowsAffected == 0 {
		return errors.New("ride status conflict: ride may have been updated concurrently")
	}
	return nil
}

func (r *RideRepo) UpdateRideWithVersion(id int64, version int, updates map[string]interface{}) error {
	updates["version"] = gorm.Expr("version + 1")
	result := r.db.Model(&model.Ride{}).
		Where("id = ? AND version = ?", id, version).
		Updates(updates)
	if result.Error != nil {
		return result.Error
	}
	if result.RowsAffected == 0 {
		return errors.New("version conflict: ride may have been updated concurrently")
	}
	return nil
}

func (r *RideRepo) GetActiveRideByPassenger(passengerID string) (*model.Ride, error) {
	var ride model.Ride
	err := r.db.Where("passenger_id = ? AND status NOT IN (?, ?)",
		passengerID, model.RideStatusCompleted, model.RideStatusCancelled).
		First(&ride).Error
	if err != nil {
		if errors.Is(err, gorm.ErrRecordNotFound) {
			return nil, nil
		}
		return nil, err
	}
	return &ride, nil
}

func (r *RideRepo) GetPendingRides() ([]model.Ride, error) {
	var rides []model.Ride
	err := r.db.Where("status = ?", model.RideStatusPending).
		Order("created_at ASC").
		Clauses(clause.Locking{Strength: "UPDATE", Options: "SKIP LOCKED"}).
		Limit(10).
		Find(&rides).Error
	return rides, err
}
