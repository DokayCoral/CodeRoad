package model

import "time"

// Ride status constants
const (
	RideStatusPending   = 0
	RideStatusMatched   = 1
	RideStatusAccepted  = 2
	RideStatusArrived   = 3
	RideStatusStarted   = 4
	RideStatusCompleted = 5
	RideStatusCancelled = 6
)

// Driver status constants
const (
	DriverStatusOffline = 0
	DriverStatusOnline  = 1
	DriverStatusBusy    = 2
)

type Ride struct {
	ID          int64     `gorm:"primaryKey;autoIncrement" json:"id"`
	PassengerID string    `gorm:"type:varchar(64);index;not null" json:"passenger_id"`
	DriverID    string    `gorm:"type:varchar(64);index" json:"driver_id"`
	OriginLng   float64   `gorm:"type:decimal(10,7);not null" json:"origin_lng"`
	OriginLat   float64   `gorm:"type:decimal(10,7);not null" json:"origin_lat"`
	DestLng     float64   `gorm:"type:decimal(10,7);not null" json:"dest_lng"`
	DestLat     float64   `gorm:"type:decimal(10,7);not null" json:"dest_lat"`
	Status      int       `gorm:"type:tinyint;not null;default:0" json:"status"`
	Distance    int       `gorm:"type:int;not null;default:0" json:"distance"`
	Duration    int       `gorm:"type:int;not null;default:0" json:"duration"`
	Price       int       `gorm:"type:int;not null;default:0" json:"price"`
	CancelBy    string    `gorm:"type:varchar(16)" json:"cancel_by"`
	CancelReason string   `gorm:"type:varchar(255)" json:"cancel_reason"`
	Version     int       `gorm:"type:int;not null;default:0" json:"version"`
	CreatedAt   time.Time `json:"created_at"`
	UpdatedAt   time.Time `json:"updated_at"`
}

type Driver struct {
	ID     string  `gorm:"type:varchar(64);primaryKey" json:"id"`
	Name   string  `gorm:"type:varchar(32);not null" json:"name"`
	Status int     `gorm:"type:tinyint;not null;default:0" json:"status"`
	Lng    float64 `gorm:"type:decimal(10,7);not null;default:0" json:"lng"`
	Lat    float64 `gorm:"type:decimal(10,7);not null;default:0" json:"lat"`
}
