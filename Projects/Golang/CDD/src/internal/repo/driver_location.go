package repo

import (
	"context"
	"time"

	"github.com/redis/go-redis/v9"
)

const driverGeoKey = "drivers:location"
const matchLockKey = "matching:lock:"
const matchLockTTL = 10 * time.Second

type DriverLocationRepo struct {
	rdb *redis.Client
}

func NewDriverLocationRepo(rdb *redis.Client) *DriverLocationRepo {
	return &DriverLocationRepo{rdb: rdb}
}

func (r *DriverLocationRepo) AddDriverLocation(ctx context.Context, driverID string, lng, lat float64) error {
	return r.rdb.GeoAdd(ctx, driverGeoKey, &redis.GeoLocation{
		Name:      driverID,
		Longitude: lng,
		Latitude:  lat,
	}).Err()
}

func (r *DriverLocationRepo) RemoveDriverLocation(ctx context.Context, driverID string) error {
	return r.rdb.ZRem(ctx, driverGeoKey, driverID).Err()
}

func (r *DriverLocationRepo) SearchNearbyDrivers(ctx context.Context, lng, lat, radius float64) ([]redis.GeoLocation, error) {
	return r.rdb.GeoRadius(ctx, driverGeoKey, lng, lat, &redis.GeoRadiusQuery{
		Radius:    radius,
		Unit:      "km",
		WithCoord: true,
		WithDist:  true,
		Sort:      "ASC",
		Count:     10,
	}).Result()
}

// TryLockMatch attempts to acquire a distributed lock on a driver for matching.
func (r *DriverLocationRepo) TryLockMatch(ctx context.Context, driverID string) (bool, error) {
	ok, err := r.rdb.SetNX(ctx, matchLockKey+driverID, "1", matchLockTTL).Result()
	return ok, err
}

// UnlockMatch releases the matching lock.
func (r *DriverLocationRepo) UnlockMatch(ctx context.Context, driverID string) error {
	return r.rdb.Del(ctx, matchLockKey+driverID).Err()
}
