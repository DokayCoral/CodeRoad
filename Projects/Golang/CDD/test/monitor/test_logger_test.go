package monitor

import (
	"sync"
	"testing"
	"time"

	cddlog "cdd/src/pkg/log"
)

// mockWriter captures log entries for assertion.
type mockWriter struct {
	mu      sync.Mutex
	entries []cddlog.Entry
}

func (m *mockWriter) Write(entry cddlog.Entry) error {
	m.mu.Lock()
	defer m.mu.Unlock()
	m.entries = append(m.entries, entry)
	return nil
}

func (m *mockWriter) Close() error { return nil }

func (m *mockWriter) getEntries() []cddlog.Entry {
	m.mu.Lock()
	defer m.mu.Unlock()
	cp := make([]cddlog.Entry, len(m.entries))
	copy(cp, m.entries)
	return cp
}

func TestTestLogger_LogTestStart(t *testing.T) {
	mw := &mockWriter{}
	logger := cddlog.New(cddlog.DEBUG, mw)
	tl := NewTestLogger(logger)

	tl.LogTestStart("TestPricing")

	entries := mw.getEntries()
	if len(entries) != 1 {
		t.Fatalf("expected 1 entry, got %d", len(entries))
	}
	if entries[0].Level != cddlog.INFO {
		t.Errorf("expected INFO level, got %s", entries[0].Level)
	}
	if entries[0].Module != "" {
		t.Errorf("expected empty module (set by DefaultLogger), got %q", entries[0].Module)
	}
}

func TestTestLogger_LogTestResult_Pass(t *testing.T) {
	mw := &mockWriter{}
	logger := cddlog.New(cddlog.DEBUG, mw)
	tl := NewTestLogger(logger)

	tl.LogTestResult("TestPricing", true, 150*time.Millisecond)

	entries := mw.getEntries()
	if len(entries) != 1 {
		t.Fatalf("expected 1 entry, got %d", len(entries))
	}

	entry := entries[0]
	if entry.Level != cddlog.INFO {
		t.Errorf("PASS should be INFO level, got %s", entry.Level)
	}
	if entry.Fields["result"] != "PASS" {
		t.Errorf("expected PASS, got %v", entry.Fields["result"])
	}
	if entry.Fields["method"] != "TestPricing" {
		t.Errorf("expected method 'TestPricing', got %v", entry.Fields["method"])
	}
	if entry.Fields["duration_ms"] != int64(150) {
		t.Errorf("expected duration_ms=150, got %v", entry.Fields["duration_ms"])
	}
}

func TestTestLogger_LogTestResult_Fail(t *testing.T) {
	mw := &mockWriter{}
	logger := cddlog.New(cddlog.DEBUG, mw)
	tl := NewTestLogger(logger)

	tl.LogTestResult("TestInvalidPath", false, 50*time.Millisecond)

	entries := mw.getEntries()
	if len(entries) != 1 {
		t.Fatalf("expected 1 entry, got %d", len(entries))
	}

	entry := entries[0]
	if entry.Level != cddlog.ERROR {
		t.Errorf("FAIL should be ERROR level, got %s", entry.Level)
	}
	if entry.Fields["result"] != "FAIL" {
		t.Errorf("expected FAIL, got %v", entry.Fields["result"])
	}
}

func TestTestLogger_ModuleField(t *testing.T) {
	mw := &mockWriter{}
	logger := cddlog.New(cddlog.DEBUG, mw)
	tl := NewTestLogger(logger)

	tl.LogTestResult("TestMethod", true, 0)

	entries := mw.getEntries()
	if len(entries) != 1 {
		t.Fatalf("expected 1 entry, got %d", len(entries))
	}
	if entries[0].Module != "test" {
		t.Errorf("expected module 'test', got %q", entries[0].Module)
	}
}

func TestTestLogFile_Path(t *testing.T) {
	path := TestLogFile()
	if path == "" {
		t.Error("log file path should not be empty")
	}
	// Should follow the pattern: logs/test_YYYYMMDD.log
	if len(path) < 10 {
		t.Errorf("path too short: %s", path)
	}
}
