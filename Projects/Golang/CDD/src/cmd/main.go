package main

import (
	"context"
	"log"
	"os"
	"os/signal"
	"syscall"

	"cdd/src/internal/config"
	"cdd/src/internal/handler"
	"cdd/src/internal/model"
	"cdd/src/internal/repo"
	"cdd/src/internal/service"
	"cdd/src/pkg/mq"

	"github.com/gin-gonic/gin"
	"github.com/redis/go-redis/v9"
	"gorm.io/driver/mysql"
	"gorm.io/gorm"
)

func main() {
	cfg := config.Load()

	// Database
	db, err := gorm.Open(mysql.Open(cfg.DB.DSN), &gorm.Config{})
	if err != nil {
		log.Fatalf("failed to connect database: %v", err)
	}
	log.Println("database connected")

	if err := db.AutoMigrate(&model.Ride{}, &model.Driver{}); err != nil {
		log.Fatalf("failed to migrate database: %v", err)
	}
	log.Println("database migrated")

	// Redis
	rdb := redis.NewClient(&redis.Options{
		Addr:     cfg.Redis.Addr,
		Password: cfg.Redis.Password,
		DB:       cfg.Redis.DB,
	})
	log.Println("redis connected")

	// RabbitMQ
	mqClient, err := mq.NewClient(cfg.RabbitMQ.URL)
	if err != nil {
		log.Fatalf("failed to connect rabbitmq: %v", err)
	}
	defer mqClient.Close()
	log.Println("rabbitmq connected")

	// Repositories
	rideRepo := repo.NewRideRepo(db)
	driverRepo := repo.NewDriverRepo(db)
	driverLocationRepo := repo.NewDriverLocationRepo(rdb)

	// Services
	pricingService := service.NewPricingService(cfg.Pricing)
	rideService := service.NewRideService(rideRepo, pricingService, mqClient)
	lifecycleService := service.NewLifecycleService(rideRepo, pricingService, mqClient)
	matchingService := service.NewMatchingService(rideRepo, driverRepo, driverLocationRepo, mqClient)

	// Start matching service consumer
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	if err := matchingService.Start(ctx); err != nil {
		log.Fatalf("failed to start matching service: %v", err)
	}

	// HTTP router
	router := gin.Default()
	handler.RegisterRoutes(router, rideRepo, driverRepo, driverLocationRepo, rideService, lifecycleService)

	// Graceful shutdown
	go func() {
		quit := make(chan os.Signal, 1)
		signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
		<-quit
		log.Println("shutting down...")
		cancel()
	}()

	log.Println("server starting on :8080")
	if err := router.Run(":8080"); err != nil {
		log.Fatalf("failed to start server: %v", err)
	}
}
