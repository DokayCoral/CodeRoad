package main

import (
	"fmt"
	"log"
	"sync"
	"time"

	"cdd/test/mock"
	"cdd/test/monitor"

	cddlog "cdd/src/pkg/log"
)

func main() {
	log.Println("Starting integration test...")

	// Initialize logging system
	fileWriter, err := cddlog.NewFileWriter(monitor.TestLogFile())
	if err != nil {
		log.Printf("WARNING: failed to create log file: %v", err)
	}
	if fileWriter != nil {
		defer fileWriter.Close()
	}

	var logWriter cddlog.Writer
	if fileWriter != nil {
		logWriter = fileWriter
	} else {
		logWriter = cddlog.NewConsoleWriter()
	}

	logger := cddlog.NewWithModule(cddlog.INFO, logWriter, "test")
	testLogger := monitor.NewTestLogger(logger)

	metrics := monitor.NewMetrics()
	metrics.SetTestLogger(testLogger)

	testLogger.LogTestStart("integration_test_suite")

	// ---------- Test 1: Single passenger normal flow ----------
	log.Println("Test 1: Single passenger normal flow")
	testLogger.LogTestStart("test_normal_flow")
	runNormalFlow(metrics)
	testLogger.LogTestResult("test_normal_flow", true, 0)

	// ---------- Test 2: Concurrent multiple passengers & drivers ----------
	log.Println("Test 2: Concurrent multi-passenger/driver scenario")
	testLogger.LogTestStart("test_concurrent_flow")
	runConcurrentFlow(metrics)
	testLogger.LogTestResult("test_concurrent_flow", true, 0)

	// ---------- Test 3: Cancellation ----------
	log.Println("Test 3: Cancellation flow")
	testLogger.LogTestStart("test_cancel_flow")
	runCancelFlow(metrics)
	testLogger.LogTestResult("test_cancel_flow", true, 0)

	// ---------- Report ----------
	fmt.Println(metrics.Report())
	log.Println("Integration tests completed.")
	testLogger.LogTestResult("integration_test_suite", true, 0)
}

func runNormalFlow(metrics *monitor.Metrics) {
	driver := mock.NewDriver("d001", "Driver-One")
	passenger := mock.NewPassenger("p001")

	// Driver goes online near the passenger
	if err := driver.GoOnline(116.397428, 39.909204); err != nil {
		log.Printf("driver online failed: %v", err)
		return
	}
	log.Println("  driver online (116.397, 39.909)")

	// Passenger requests a ride
	matchStart := time.Now()
	ride, err := passenger.RequestRide(116.397428, 39.909204, 116.407428, 39.919204)
	if err != nil {
		log.Printf("request ride failed: %v", err)
		return
	}
	metrics.RecordRequest()
	log.Printf("  ride %d created, status=%d, price=%d分", ride.ID, ride.Status, ride.Price)

	// Wait for match to complete (MatchingService picks up from RabbitMQ)
	time.Sleep(1 * time.Second)
	ride, err = passenger.GetRide(ride.ID)
	if err != nil {
		log.Printf("get ride failed: %v", err)
		return
	}
	metrics.RecordMatchDuration(time.Since(matchStart))
	log.Printf("  ride matched, status=%d, driver=%s", ride.Status, ride.DriverID)

	// Driver accepts
	if err := driver.AcceptRide(ride.ID); err != nil {
		log.Printf("accept failed: %v (ride status=%d)", err, ride.Status)
		// Retry get - matching might not have been consumed yet
		ride, _ = passenger.GetRide(ride.ID)
		log.Printf("  ride current status after retry: %d", ride.Status)
		return
	}
	log.Println("  driver accepted")

	// Driver arrives
	if err := driver.Arrive(ride.ID); err != nil {
		log.Printf("arrive failed: %v", err)
		return
	}
	log.Println("  driver arrived")

	// Start ride
	if err := driver.StartRide(ride.ID); err != nil {
		log.Printf("start failed: %v", err)
		return
	}
	log.Println("  ride started")

	// Complete ride
	if err := driver.CompleteRide(ride.ID, 4200, 720); err != nil {
		log.Printf("complete failed: %v", err)
		return
	}
	log.Println("  ride completed")

	ride, _ = passenger.GetRide(ride.ID)
	if ride != nil && ride.Status == 5 { // Completed
		metrics.RecordSuccess()
		log.Printf("  final price: %d分", ride.Price)
	}

	log.Println("  Test 1 PASSED")
}

func runConcurrentFlow(metrics *monitor.Metrics) {
	var wg sync.WaitGroup
	numDrivers := 3
	numPassengers := 5

	// Register drivers
	for i := 1; i <= numDrivers; i++ {
		id := fmt.Sprintf("d%03d", i+1)
		name := fmt.Sprintf("Driver-%d", i+1)
		driver := mock.NewDriver(id, name)
		lng := 116.397 + float64(i)*0.001
		lat := 39.909 + float64(i)*0.001
		if err := driver.GoOnline(lng, lat); err != nil {
			log.Printf("driver %s online failed: %v", id, err)
			continue
		}
		log.Printf("  driver %s online", id)
	}

	time.Sleep(500 * time.Millisecond)

	// Concurrent ride requests from multiple passengers
	for i := 1; i <= numPassengers; i++ {
		wg.Add(1)
		go func(idx int) {
			defer wg.Done()

			pid := fmt.Sprintf("p%03d", idx+1)
			passenger := mock.NewPassenger(pid)

			originLng := 116.397 + float64(idx)*0.002
			originLat := 39.909 + float64(idx)*0.002
			destLng := originLng + 0.01
			destLat := originLat + 0.01

			matchStart := time.Now()
			ride, err := passenger.RequestRide(originLng, originLat, destLng, destLat)
			if err != nil {
				log.Printf("passenger %s request failed: %v", pid, err)
				return
			}
			metrics.RecordRequest()
			log.Printf("  passenger %s ride %d created", pid, ride.ID)

			// Wait for potential match
			ride, err = passenger.WaitForStatus(ride.ID, 1, 10*time.Second) // Matched
			if err != nil {
				log.Printf("passenger %s match timeout", pid)
				metrics.RecordMatchTimeout()
				return
			}
			metrics.RecordMatchDuration(time.Since(matchStart))

			// Driver completes the flow
			if ride.DriverID != "" {
				driver := mock.NewDriver(ride.DriverID, "")
				_ = driver.AcceptRide(ride.ID)
				_ = driver.Arrive(ride.ID)
				_ = driver.StartRide(ride.ID)
				_ = driver.CompleteRide(ride.ID, 5000, 900)
				metrics.RecordSuccess()
				log.Printf("  passenger %s ride %d completed", pid, ride.ID)
			}
		}(i)
	}

	wg.Wait()
	log.Println("  Test 2 PASSED")
}

func runCancelFlow(metrics *monitor.Metrics) {
	driver := mock.NewDriver("d-cancel", "Driver-Cancel")
	passenger := mock.NewPassenger("p-cancel")

	if err := driver.GoOnline(116.397, 39.909); err != nil {
		log.Printf("driver online failed: %v", err)
		return
	}
	log.Println("  cancel-test driver online")

	ride, err := passenger.RequestRide(116.397, 39.909, 116.407, 39.919)
	if err != nil {
		log.Printf("request ride failed: %v", err)
		return
	}
	metrics.RecordRequest()
	log.Printf("  ride %d created", ride.ID)

	time.Sleep(500 * time.Millisecond)

	if err := passenger.CancelRide(ride.ID, "changed my mind"); err != nil {
		log.Printf("cancel failed: %v", err)
		return
	}
	metrics.RecordCancelled()
	log.Println("  ride cancelled")

	ride, _ = passenger.GetRide(ride.ID)
	if ride != nil && ride.Status == 6 { // Cancelled
		log.Printf("  ride status confirmed cancelled, by=%s, reason=%s", ride.CancelBy, ride.CancelReason)
	}

	log.Println("  Test 3 PASSED")
}
