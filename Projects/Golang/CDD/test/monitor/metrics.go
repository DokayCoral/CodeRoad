package monitor

import (
	"fmt"
	"sync"
	"time"
)

// Metrics collects system runtime metrics.
type Metrics struct {
	mu sync.Mutex

	TotalRequests   int
	SuccessfulRides int
	CancelledRides  int
	MatchTimeouts   int
	MatchDurations  []time.Duration

	testLogger *TestLogger
	startTime  time.Time
}

func NewMetrics() *Metrics {
	return &Metrics{
		startTime: time.Now(),
	}
}

func (m *Metrics) SetTestLogger(tl *TestLogger) {
	m.mu.Lock()
	defer m.mu.Unlock()
	m.testLogger = tl
}

func (m *Metrics) RecordRequest() {
	m.mu.Lock()
	defer m.mu.Unlock()
	m.TotalRequests++
	if m.testLogger != nil {
		m.testLogger.LogTestStart(fmt.Sprintf("total_requests=%d", m.TotalRequests))
	}
}

func (m *Metrics) RecordSuccess() {
	m.mu.Lock()
	defer m.mu.Unlock()
	m.SuccessfulRides++
	if m.testLogger != nil {
		m.testLogger.LogTestResult(
			fmt.Sprintf("ride_%d", m.SuccessfulRides),
			true,
			0,
		)
	}
}

func (m *Metrics) RecordCancelled() {
	m.mu.Lock()
	defer m.mu.Unlock()
	m.CancelledRides++
	if m.testLogger != nil {
		m.testLogger.LogTestResult(
			fmt.Sprintf("cancel_%d", m.CancelledRides),
			true,
			0,
		)
	}
}

func (m *Metrics) RecordMatchTimeout() {
	m.mu.Lock()
	defer m.mu.Unlock()
	m.MatchTimeouts++
	if m.testLogger != nil {
		m.testLogger.LogTestStart(fmt.Sprintf("match_timeout_%d", m.MatchTimeouts))
	}
}

func (m *Metrics) RecordMatchDuration(d time.Duration) {
	m.mu.Lock()
	defer m.mu.Unlock()
	m.MatchDurations = append(m.MatchDurations, d)
}

// Report prints a summary of collected metrics.
func (m *Metrics) Report() string {
	m.mu.Lock()
	defer m.mu.Unlock()

	elapsed := time.Since(m.startTime)
	var avgMatch time.Duration
	if len(m.MatchDurations) > 0 {
		var total time.Duration
		for _, d := range m.MatchDurations {
			total += d
		}
		avgMatch = total / time.Duration(len(m.MatchDurations))
	}

	completeRate := 0.0
	if m.TotalRequests > 0 {
		completeRate = float64(m.SuccessfulRides) / float64(m.TotalRequests) * 100
	}

	report := fmt.Sprintf(`
=== System Metrics ===
Elapsed:          %v
Total Requests:   %d
Successful Rides: %d
Cancelled Rides:  %d
Match Timeouts:   %d
Completion Rate:  %.1f%%
Avg Match Time:   %v
====================
`, elapsed, m.TotalRequests, m.SuccessfulRides, m.CancelledRides,
		m.MatchTimeouts, completeRate, avgMatch)

	if m.testLogger != nil {
		m.testLogger.LogTestStart("metrics_report")
	}

	return report
}
