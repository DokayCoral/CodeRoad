package log

import (
	"bytes"
	"fmt"
	"os"
	"path/filepath"
	"sync"
	"testing"
)

// ---------- 6.1 Level and Entry tests ----------

func TestLevelString(t *testing.T) {
	tests := []struct {
		level    Level
		expected string
	}{
		{DEBUG, "DEBUG"},
		{INFO, "INFO"},
		{WARN, "WARN"},
		{ERROR, "ERROR"},
		{Level(99), "UNKNOWN"},
	}

	for _, tc := range tests {
		if got := tc.level.String(); got != tc.expected {
			t.Errorf("Level(%d).String() = %q, want %q", tc.level, got, tc.expected)
		}
	}
}

func TestEntryCreation(t *testing.T) {
	entry := Entry{
		Level:   INFO,
		Module:  "test",
		Message: "hello",
		Fields:  map[string]interface{}{"key": "value"},
	}

	if entry.Level != INFO {
		t.Error("entry level mismatch")
	}
	if entry.Module != "test" {
		t.Error("entry module mismatch")
	}
	if entry.Fields["key"] != "value" {
		t.Error("entry fields mismatch")
	}
}

// ---------- 6.2 ConsoleWriter tests ----------

func TestConsoleWriter_Format(t *testing.T) {
	var buf bytes.Buffer
	cw := &ConsoleWriter{out: &buf}

	entry := Entry{
		Level:   INFO,
		Module:  "test",
		Message: "hello world",
	}

	if err := cw.Write(entry); err != nil {
		t.Fatalf("write failed: %v", err)
	}

	output := buf.String()
	if output == "" {
		t.Error("output should not be empty")
	}
}

func TestConsoleWriter_WithFields(t *testing.T) {
	var buf bytes.Buffer
	cw := &ConsoleWriter{out: &buf}

	entry := Entry{
		Level:   ERROR,
		Module:  "test",
		Message: "failure",
		Fields:  map[string]interface{}{"result": "FAIL"},
	}

	if err := cw.Write(entry); err != nil {
		t.Fatalf("write failed: %v", err)
	}

	output := buf.String()
	if output == "" {
		t.Error("output should not be empty")
	}
}

func TestConsoleWriter_Close(t *testing.T) {
	cw := NewConsoleWriter()
	if err := cw.Close(); err != nil {
		t.Errorf("close should not error: %v", err)
	}
}

// ---------- 6.3 FileWriter tests ----------

func TestFileWriter_WriteAndRead(t *testing.T) {
	dir := t.TempDir()
	path := filepath.Join(dir, "test.log")

	fw, err := NewFileWriter(path)
	if err != nil {
		t.Fatalf("create FileWriter: %v", err)
	}

	entry := Entry{
		Level:   INFO,
		Module:  "test",
		Message: "file test",
	}

	if err := fw.Write(entry); err != nil {
		t.Fatalf("write: %v", err)
	}
	fw.Close()

	data, err := os.ReadFile(path)
	if err != nil {
		t.Fatalf("read file: %v", err)
	}
	if len(data) == 0 {
		t.Error("file should not be empty after write")
	}
}

func TestFileWriter_Append(t *testing.T) {
	dir := t.TempDir()
	path := filepath.Join(dir, "append.log")

	fw, _ := NewFileWriter(path)
	fw.Write(Entry{Level: INFO, Module: "a", Message: "first"})
	fw.Close()

	fw2, _ := NewFileWriter(path)
	fw2.Write(Entry{Level: INFO, Module: "b", Message: "second"})
	fw2.Close()

	data, _ := os.ReadFile(path)
	lines := bytes.Count(data, []byte("\n"))
	if lines < 2 {
		t.Errorf("expected at least 2 lines, got %d", lines)
	}
}

func TestFileWriter_Concurrency(t *testing.T) {
	dir := t.TempDir()
	path := filepath.Join(dir, "concurrent.log")

	fw, _ := NewFileWriter(path)
	defer fw.Close()

	var wg sync.WaitGroup
	numWriters := 10
	numEntries := 50

	for i := 0; i < numWriters; i++ {
		wg.Add(1)
		go func(id int) {
			defer wg.Done()
			for j := 0; j < numEntries; j++ {
				fw.Write(Entry{
					Level:   INFO,
					Module:  "concurrent",
					Message: fmt.Sprintf("writer_%d_entry_%d", id, j),
				})
			}
		}(i)
	}
	wg.Wait()
	fw.Close()

	data, _ := os.ReadFile(path)
	lines := bytes.Count(data, []byte("\n"))
	expected := numWriters * numEntries
	if lines != expected {
		t.Errorf("expected %d lines, got %d", expected, lines)
	}
}

func TestFileWriter_AutoCreateDir(t *testing.T) {
	dir := t.TempDir()
	nestedPath := filepath.Join(dir, "sub", "nested", "test.log")

	fw, err := NewFileWriter(nestedPath)
	if err != nil {
		t.Fatalf("create FileWriter with nested dir: %v", err)
	}
	fw.Close()

	if _, err := os.Stat(nestedPath); os.IsNotExist(err) {
		t.Error("log file should exist after auto-create")
	}
}

// ---------- 6.4 DefaultLogger level filtering tests ----------

type mockWriter struct {
	entries []Entry
}

func (m *mockWriter) Write(entry Entry) error {
	m.entries = append(m.entries, entry)
	return nil
}

func (m *mockWriter) Close() error { return nil }

func TestDefaultLogger_LevelFilter(t *testing.T) {
	mw := &mockWriter{}
	logger := New(INFO, mw)

	logger.Debug("should be filtered")
	logger.Info("should appear")
	logger.Warn("should appear too")
	logger.Error("should appear three")

	if len(mw.entries) != 3 {
		t.Errorf("expected 3 entries (DEBUG filtered), got %d", len(mw.entries))
	}

	if mw.entries[0].Level != INFO {
		t.Errorf("first entry should be INFO, got %s", mw.entries[0].Level)
	}
}

func TestDefaultLogger_ErrorLevel(t *testing.T) {
	mw := &mockWriter{}
	logger := New(ERROR, mw)

	logger.Debug("filtered")
	logger.Info("filtered")
	logger.Warn("filtered")
	logger.Error("only this")

	if len(mw.entries) != 1 {
		t.Errorf("expected 1 entry, got %d", len(mw.entries))
	}
}

func TestDefaultLogger_LogEntry(t *testing.T) {
	mw := &mockWriter{}
	logger := New(DEBUG, mw)

	logger.LogEntry(Entry{
		Level:   INFO,
		Module:  "custom",
		Message: "structured",
		Fields:  map[string]interface{}{"x": 1},
	})

	if len(mw.entries) != 1 {
		t.Fatalf("expected 1 entry, got %d", len(mw.entries))
	}
	if mw.entries[0].Module != "custom" {
		t.Errorf("module: expected 'custom', got %q", mw.entries[0].Module)
	}
}

func TestDefaultLogger_ModuleOverride(t *testing.T) {
	mw := &mockWriter{}
	logger := NewWithModule(DEBUG, mw, "my-module")

	logger.Info("test message")

	if len(mw.entries) != 1 {
		t.Fatalf("expected 1 entry, got %d", len(mw.entries))
	}
	if mw.entries[0].Module != "my-module" {
		t.Errorf("module: expected 'my-module', got %q", mw.entries[0].Module)
	}
}

// ---------- 6.6 Interface contract test ----------

// Verify that TestLogger can work with any Logger implementation.
func TestInterfaceContract_MockWriter(t *testing.T) {
	mw := &mockWriter{}
	logger := New(DEBUG, mw)

	// Simulate what TestLogger does
	logger.Info("test started: %s", "TestMethod")
	logger.LogEntry(Entry{
		Level:   INFO,
		Time:    Entry{}.Time, // zero time
		Module:  "test",
		Message: "test completed: TestMethod",
		Fields: map[string]interface{}{
			"method":       "TestMethod",
			"result":       "PASS",
			"duration_ms": int64(150),
		},
	})

	if len(mw.entries) != 2 {
		t.Fatalf("expected 2 entries, got %d", len(mw.entries))
	}
	if mw.entries[1].Fields["result"] != "PASS" {
		t.Error("field 'result' mismatch")
	}
}
