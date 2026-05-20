package repo

import (
	"errors"

	"cdd/src/internal/model"

	"gorm.io/gorm"
)

type DriverRepo struct {
	db *gorm.DB
}

func NewDriverRepo(db *gorm.DB) *DriverRepo {
	return &DriverRepo{db: db}
}

func (r *DriverRepo) UpdateDriverStatus(driverID string, status int) error {
	result := r.db.Model(&model.Driver{}).
		Where("id = ?", driverID).
		Update("status", status)
	if result.Error != nil {
		return result.Error
	}
	if result.RowsAffected == 0 {
		return errors.New("driver not found")
	}
	return nil
}

func (r *DriverRepo) UpdateDriverLocation(driverID string, lng, lat float64) error {
	result := r.db.Model(&model.Driver{}).
		Where("id = ?", driverID).
		Updates(map[string]interface{}{
			"lng": lng,
			"lat": lat,
		})
	if result.Error != nil {
		return result.Error
	}
	if result.RowsAffected == 0 {
		return errors.New("driver not found")
	}
	return nil
}

func (r *DriverRepo) GetDriverByID(driverID string) (*model.Driver, error) {
	var driver model.Driver
	if err := r.db.First(&driver, "id = ?", driverID).Error; err != nil {
		if errors.Is(err, gorm.ErrRecordNotFound) {
			return nil, nil
		}
		return nil, err
	}
	return &driver, nil
}

func (r *DriverRepo) CreateDriver(driver *model.Driver) error {
	return r.db.Create(driver).Error
}
