package mock

import (
	"encoding/json"
	"fmt"
	"time"

	"github.com/go-resty/resty/v2"
)

const baseURL = "http://127.0.0.1:8080/api/v1"

type Passenger struct {
	ID     string
	client *resty.Client
}

type RideResponse struct {
	ID          int64   `json:"id"`
	PassengerID string  `json:"passenger_id"`
	DriverID    string  `json:"driver_id"`
	Status      int     `json:"status"`
	Price       int     `json:"price"`
	Distance     int    `json:"distance"`
	Duration     int    `json:"duration"`
	CancelBy     string `json:"cancel_by"`
	CancelReason string `json:"cancel_reason"`
}

func NewPassenger(id string) *Passenger {
	return &Passenger{
		ID:     id,
		client: resty.New().SetTimeout(10 * time.Second),
	}
}

// RequestRide sends a ride request and returns the created ride.
func (p *Passenger) RequestRide(originLng, originLat, destLng, destLat float64) (*RideResponse, error) {
	resp, err := p.client.R().
		SetBody(map[string]interface{}{
			"passenger_id": p.ID,
			"origin_lng":   originLng,
			"origin_lat":   originLat,
			"dest_lng":     destLng,
			"dest_lat":     destLat,
		}).
		Post(baseURL + "/rides")
	if err != nil {
		return nil, fmt.Errorf("request ride failed: %w", err)
	}
	if resp.StatusCode() != 201 {
		return nil, fmt.Errorf("request ride returned %d: %s", resp.StatusCode(), resp.Body())
	}

	var ride RideResponse
	if err := json.Unmarshal(resp.Body(), &ride); err != nil {
		return nil, fmt.Errorf("unmarshal ride response: %w", err)
	}
	return &ride, nil
}

// GetRide polls the ride status until it changes or timeout.
func (p *Passenger) GetRide(rideID int64) (*RideResponse, error) {
	resp, err := p.client.R().
		Get(fmt.Sprintf("%s/rides/%d", baseURL, rideID))
	if err != nil {
		return nil, err
	}
	if resp.StatusCode() != 200 {
		return nil, fmt.Errorf("get ride returned %d: %s", resp.StatusCode(), resp.Body())
	}

	var ride RideResponse
	if err := json.Unmarshal(resp.Body(), &ride); err != nil {
		return nil, err
	}
	return &ride, nil
}

// CancelRide cancels a pending or matched ride.
func (p *Passenger) CancelRide(rideID int64, reason string) error {
	resp, err := p.client.R().
		SetBody(map[string]interface{}{
			"cancelled_by": p.ID,
			"reason":       reason,
		}).
		Post(fmt.Sprintf("%s/rides/%d/cancel", baseURL, rideID))
	if err != nil {
		return err
	}
	if resp.StatusCode() != 200 {
		return fmt.Errorf("cancel ride returned %d: %s", resp.StatusCode(), resp.Body())
	}
	return nil
}

// WaitForStatus polls until the ride reaches expectedStatus or times out.
func (p *Passenger) WaitForStatus(rideID int64, expectedStatus int, timeout time.Duration) (*RideResponse, error) {
	deadline := time.Now().Add(timeout)
	for time.Now().Before(deadline) {
		ride, err := p.GetRide(rideID)
		if err != nil {
			time.Sleep(500 * time.Millisecond)
			continue
		}
		if ride.Status == expectedStatus {
			return ride, nil
		}
		time.Sleep(500 * time.Millisecond)
	}
	return nil, fmt.Errorf("timeout waiting for status %d", expectedStatus)
}
