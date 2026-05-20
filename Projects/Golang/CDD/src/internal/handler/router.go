package handler

import (
	"cdd/src/internal/repo"
	"cdd/src/internal/service"

	"github.com/gin-gonic/gin"
)

func RegisterRoutes(
	router *gin.Engine,
	rideRepo *repo.RideRepo,
	driverRepo *repo.DriverRepo,
	driverLocationRepo *repo.DriverLocationRepo,
	rideService *service.RideService,
	lifecycleService *service.LifecycleService,
) {
	passengerH := NewPassengerHandler(rideService, lifecycleService, rideRepo)
	driverH := NewDriverHandler(lifecycleService, driverRepo, driverLocationRepo)

	api := router.Group("/api/v1")
	{
		// Passenger endpoints
		api.POST("/rides", passengerH.CreateRide)
		api.GET("/rides/:id", passengerH.GetRide)
		api.POST("/rides/:id/cancel", passengerH.CancelRide)

		// Driver endpoints
		api.POST("/rides/:id/accept", driverH.Accept)
		api.POST("/rides/:id/arrive", driverH.Arrive)
		api.POST("/rides/:id/start", driverH.Start)
		api.POST("/rides/:id/complete", driverH.Complete)
		api.POST("/drivers", driverH.RegisterDriver)
		api.POST("/drivers/location", driverH.UpdateLocation)
		api.POST("/drivers/status", driverH.UpdateStatus)
		api.GET("/drivers/nearby", driverH.NearbyDrivers)
	}
}
