package handler

import (
	"net/http"
	"strconv"

	"cdd/src/internal/repo"
	"cdd/src/internal/service"

	"github.com/gin-gonic/gin"
)

type PassengerHandler struct {
	rideService      *service.RideService
	lifecycleService *service.LifecycleService
	rideRepo         *repo.RideRepo
}

func NewPassengerHandler(
	rideService *service.RideService,
	lifecycleService *service.LifecycleService,
	rideRepo *repo.RideRepo,
) *PassengerHandler {
	return &PassengerHandler{
		rideService:      rideService,
		lifecycleService: lifecycleService,
		rideRepo:         rideRepo,
	}
}

type createRideReq struct {
	PassengerID string  `json:"passenger_id" binding:"required"`
	OriginLng   float64 `json:"origin_lng" binding:"required"`
	OriginLat   float64 `json:"origin_lat" binding:"required"`
	DestLng     float64 `json:"dest_lng" binding:"required"`
	DestLat     float64 `json:"dest_lat" binding:"required"`
}

func (h *PassengerHandler) CreateRide(c *gin.Context) {
	var req createRideReq
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusUnprocessableEntity, gin.H{"error": "invalid parameters: " + err.Error()})
		return
	}

	ride, err := h.rideService.HandleRideRequest(c.Request.Context(), service.RideRequest{
		PassengerID: req.PassengerID,
		OriginLng:   req.OriginLng,
		OriginLat:   req.OriginLat,
		DestLng:     req.DestLng,
		DestLat:     req.DestLat,
	})
	if err != nil {
		c.JSON(http.StatusConflict, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusCreated, ride)
}

func (h *PassengerHandler) GetRide(c *gin.Context) {
	id, err := strconv.ParseInt(c.Param("id"), 10, 64)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid ride id"})
		return
	}

	ride, err := h.rideRepo.GetRideByID(id)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	if ride == nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "ride not found"})
		return
	}

	c.JSON(http.StatusOK, ride)
}

type cancelReq struct {
	CancelledBy string `json:"cancelled_by" binding:"required"`
	Reason      string `json:"reason"`
}

func (h *PassengerHandler) CancelRide(c *gin.Context) {
	id, err := strconv.ParseInt(c.Param("id"), 10, 64)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid ride id"})
		return
	}

	var req cancelReq
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusUnprocessableEntity, gin.H{"error": "invalid parameters"})
		return
	}

	if err := h.lifecycleService.Cancel(id, req.CancelledBy, req.Reason); err != nil {
		c.JSON(http.StatusConflict, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{"status": "cancelled"})
}
