package mock

import (
	"fmt"
	"time"

	"github.com/go-resty/resty/v2"
)

type Driver struct {
	ID     string
	Name   string
	client *resty.Client
}

func NewDriver(id, name string) *Driver {
	return &Driver{
		ID:     id,
		Name:   name,
		client: resty.New().SetTimeout(10 * time.Second),
	}
}

// GoOnline registers the driver and sets status to Online with current location.
func (d *Driver) GoOnline(lng, lat float64) error {
	// Register driver
	resp, err := d.client.R().
		SetBody(map[string]interface{}{
			"id":   d.ID,
			"name": d.Name,
		}).
		Post(baseURL + "/drivers")
	if err != nil {
		return fmt.Errorf("register driver: %w", err)
	}
	if resp.StatusCode() != 201 {
		return fmt.Errorf("register driver returned %d: %s", resp.StatusCode(), resp.Body())
	}

	// Set online status (the status endpoint also adds to Redis GEO)
	resp, err = d.client.R().
		SetBody(map[string]interface{}{
			"driver_id": d.ID,
			"status":    1, // Online
		}).
		Post(baseURL + "/drivers/status")
	if err != nil {
		return err
	}
	if resp.StatusCode() != 200 {
		return fmt.Errorf("go online returned %d: %s", resp.StatusCode(), resp.Body())
	}

	// Update location
	resp, err = d.client.R().
		SetBody(map[string]interface{}{
			"driver_id": d.ID,
			"lng":       lng,
			"lat":       lat,
		}).
		Post(baseURL + "/drivers/location")
	if err != nil {
		return err
	}
	if resp.StatusCode() != 200 {
		return fmt.Errorf("update location returned %d: %s", resp.StatusCode(), resp.Body())
	}
	return nil
}

// AcceptRide accepts an assigned ride.
func (d *Driver) AcceptRide(rideID int64) error {
	resp, err := d.client.R().
		SetBody(map[string]interface{}{
			"driver_id": d.ID,
		}).
		Post(fmt.Sprintf("%s/rides/%d/accept", baseURL, rideID))
	if err != nil {
		return err
	}
	if resp.StatusCode() != 200 {
		return fmt.Errorf("accept ride returned %d: %s", resp.StatusCode(), resp.Body())
	}
	return nil
}

// Arrive marks the driver as arrived at pickup point.
func (d *Driver) Arrive(rideID int64) error {
	resp, err := d.client.R().
		SetBody(map[string]interface{}{
			"driver_id": d.ID,
		}).
		Post(fmt.Sprintf("%s/rides/%d/arrive", baseURL, rideID))
	if err != nil {
		return err
	}
	if resp.StatusCode() != 200 {
		return fmt.Errorf("arrive returned %d: %s", resp.StatusCode(), resp.Body())
	}
	return nil
}

// StartRide starts the trip.
func (d *Driver) StartRide(rideID int64) error {
	resp, err := d.client.R().
		SetBody(map[string]interface{}{
			"driver_id": d.ID,
		}).
		Post(fmt.Sprintf("%s/rides/%d/start", baseURL, rideID))
	if err != nil {
		return err
	}
	if resp.StatusCode() != 200 {
		return fmt.Errorf("start ride returned %d: %s", resp.StatusCode(), resp.Body())
	}
	return nil
}

// CompleteRide finishes the trip with actual distance and duration.
func (d *Driver) CompleteRide(rideID int64, distance, duration int) error {
	resp, err := d.client.R().
		SetBody(map[string]interface{}{
			"driver_id":       d.ID,
			"actual_distance": distance,
			"actual_duration": duration,
		}).
		Post(fmt.Sprintf("%s/rides/%d/complete", baseURL, rideID))
	if err != nil {
		return err
	}
	if resp.StatusCode() != 200 {
		return fmt.Errorf("complete ride returned %d: %s", resp.StatusCode(), resp.Body())
	}
	return nil
}
