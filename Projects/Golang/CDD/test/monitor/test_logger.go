package monitor

import (
	"fmt"
	"time"

	"cdd/src/pkg/log"
)

// TestLogger records test process logs using the core Logger interface.
type TestLogger struct {
	logger log.Logger
}

// NewTestLogger creates a TestLogger wrapping the given Logger.
func NewTestLogger(logger log.Logger) *TestLogger {
	return &TestLogger{logger: logger}
}

// LogTestStart records the start of a test method.
func (tl *TestLogger) LogTestStart(method string) {
	tl.logger.Info("test started: %s", method)
}

// LogTestResult records the result of a test method.
func (tl *TestLogger) LogTestResult(method string, passed bool, duration time.Duration) {
	result := "PASS"
	level := log.INFO
	if !passed {
		result = "FAIL"
		level = log.ERROR
	}
	tl.logger.LogEntry(log.Entry{
		Level:   level,
		Time:    time.Now(),
		Module:  "test",
		Message: fmt.Sprintf("test completed: %s", method),
		Fields: map[string]interface{}{
			"method":       method,
			"result":       result,
			"duration_ms": duration.Milliseconds(),
		},
	})
}

// TestLogFile returns the date-based log file path.
func TestLogFile() string {
	now := time.Now()
	return fmt.Sprintf("logs/test_%s.log", now.Format("20060102"))
}
