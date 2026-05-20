package log

import "time"

// Level represents the severity of a log entry.
type Level int

const (
	DEBUG Level = iota
	INFO
	WARN
	ERROR
)

func (l Level) String() string {
	switch l {
	case DEBUG:
		return "DEBUG"
	case INFO:
		return "INFO"
	case WARN:
		return "WARN"
	case ERROR:
		return "ERROR"
	default:
		return "UNKNOWN"
	}
}

// Entry is a single log record.
type Entry struct {
	Level   Level
	Time    time.Time
	Module  string
	Message string
	Fields  map[string]interface{}
}

// Writer is the output target abstraction.
type Writer interface {
	Write(entry Entry) error
	Close() error
}

// Logger is the unified logging interface.
type Logger interface {
	Debug(format string, args ...interface{})
	Info(format string, args ...interface{})
	Warn(format string, args ...interface{})
	Error(format string, args ...interface{})
	// LogEntry writes a pre-constructed Entry. Used for structured logging.
	LogEntry(entry Entry)
}
