package handler

import (
	"net/http"
	"strconv"

	"cdd/src/internal/model"
	"cdd/src/internal/repo"
	"cdd/src/internal/service"

	"github.com/gin-gonic/gin"
)

type DriverHandler struct {
	lifecycleService   *service.LifecycleService
	driverRepo         *repo.DriverRepo
	driverLocationRepo *repo.DriverLocationRepo
}

func NewDriverHandler(
	lifecycleService *service.LifecycleService,
	driverRepo *repo.DriverRepo,
	driverLocationRepo *repo.DriverLocationRepo,
) *DriverHandler {
	return &DriverHandler{
		lifecycleService:   lifecycleService,
		driverRepo:         driverRepo,
		driverLocationRepo: driverLocationRepo,
	}
}

type driverActionReq struct {
	DriverID string `json:"driver_id" binding:"required"`
}

type completeReq struct {
	DriverID       string `json:"driver_id" binding:"required"`
	ActualDistance int    `json:"actual_distance" binding:"required"`
	ActualDuration int    `json:"actual_duration" binding:"required"`
}

func (h *DriverHandler) Accept(c *gin.Context) {
	id, err := strconv.ParseInt(c.Param("id"), 10, 64)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid ride id"})
		return
	}
	var req driverActionReq
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusUnprocessableEntity, gin.H{"error": "invalid parameters"})
		return
	}

	if err := h.lifecycleService.Accept(id, req.DriverID); err != nil {
		c.JSON(http.StatusConflict, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, gin.H{"status": "accepted"})
}

func (h *DriverHandler) Arrive(c *gin.Context) {
	id, err := strconv.ParseInt(c.Param("id"), 10, 64)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid ride id"})
		return
	}
	var req driverActionReq
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusUnprocessableEntity, gin.H{"error": "invalid parameters"})
		return
	}

	if err := h.lifecycleService.Arrive(id, req.DriverID); err != nil {
		c.JSON(http.StatusConflict, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, gin.H{"status": "arrived"})
}

func (h *DriverHandler) Start(c *gin.Context) {
	id, err := strconv.ParseInt(c.Param("id"), 10, 64)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid ride id"})
		return
	}
	var req driverActionReq
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusUnprocessableEntity, gin.H{"error": "invalid parameters"})
		return
	}

	if err := h.lifecycleService.Start(id, req.DriverID); err != nil {
		c.JSON(http.StatusConflict, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, gin.H{"status": "started"})
}

func (h *DriverHandler) Complete(c *gin.Context) {
	id, err := strconv.ParseInt(c.Param("id"), 10, 64)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid ride id"})
		return
	}
	var req completeReq
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusUnprocessableEntity, gin.H{"error": "invalid parameters"})
		return
	}

	if err := h.lifecycleService.Complete(id, req.DriverID, req.ActualDistance, req.ActualDuration); err != nil {
		c.JSON(http.StatusConflict, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, gin.H{"status": "completed"})
}

type updateLocationReq struct {
	DriverID string  `json:"driver_id" binding:"required"`
	Lng      float64 `json:"lng" binding:"required"`
	Lat      float64 `json:"lat" binding:"required"`
}

type updateStatusReq struct {
	DriverID string `json:"driver_id" binding:"required"`
	Status   int    `json:"status" binding:"required"`
}

type registerDriverReq struct {
	ID   string `json:"id" binding:"required"`
	Name string `json:"name" binding:"required"`
}

func (h *DriverHandler) RegisterDriver(c *gin.Context) {
	var req registerDriverReq
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusUnprocessableEntity, gin.H{"error": "invalid parameters"})
		return
	}

	driver := &model.Driver{
		ID:   req.ID,
		Name: req.Name,
	}
	if err := h.driverRepo.CreateDriver(driver); err != nil {
		c.JSON(http.StatusConflict, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusCreated, driver)
}

func (h *DriverHandler) UpdateLocation(c *gin.Context) {
	var req updateLocationReq
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusUnprocessableEntity, gin.H{"error": "invalid parameters"})
		return
	}

	if err := h.driverRepo.UpdateDriverLocation(req.DriverID, req.Lng, req.Lat); err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": err.Error()})
		return
	}
	_ = h.driverLocationRepo.AddDriverLocation(c.Request.Context(), req.DriverID, req.Lng, req.Lat)

	c.JSON(http.StatusOK, gin.H{"status": "ok"})
}

func (h *DriverHandler) UpdateStatus(c *gin.Context) {
	var req updateStatusReq
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusUnprocessableEntity, gin.H{"error": "invalid parameters"})
		return
	}

	if err := h.driverRepo.UpdateDriverStatus(req.DriverID, req.Status); err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": err.Error()})
		return
	}

	// Sync with Redis GEO
	if req.Status == model.DriverStatusOnline {
		driver, _ := h.driverRepo.GetDriverByID(req.DriverID)
		if driver != nil {
			_ = h.driverLocationRepo.AddDriverLocation(c.Request.Context(), req.DriverID, driver.Lng, driver.Lat)
		}
	} else {
		_ = h.driverLocationRepo.RemoveDriverLocation(c.Request.Context(), req.DriverID)
	}

	c.JSON(http.StatusOK, gin.H{"status": "ok"})
}

type nearbyQuery struct {
	Lng    float64 `form:"lng" binding:"required"`
	Lat    float64 `form:"lat" binding:"required"`
	Radius float64 `form:"radius"`
}

func (h *DriverHandler) NearbyDrivers(c *gin.Context) {
	var query nearbyQuery
	if err := c.ShouldBindQuery(&query); err != nil {
		c.JSON(http.StatusUnprocessableEntity, gin.H{"error": "invalid parameters"})
		return
	}
	radius := query.Radius
	if radius <= 0 {
		radius = 3.0
	}

	drivers, err := h.driverLocationRepo.SearchNearbyDrivers(c.Request.Context(), query.Lng, query.Lat, radius)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, drivers)
}
