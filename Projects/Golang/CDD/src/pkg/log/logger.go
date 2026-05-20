package log

import (
	"fmt"
	"time"
)

// DefaultLogger implements Logger with a Writer and a minimum Level.
type DefaultLogger struct {
	level  Level
	writer Writer
	module string
}

// New creates a DefaultLogger with the given min level and writer.
func New(level Level, writer Writer) *DefaultLogger {
	return &DefaultLogger{level: level, writer: writer}
}

// NewWithModule creates a DefaultLogger with a module name.
func NewWithModule(level Level, writer Writer, module string) *DefaultLogger {
	return &DefaultLogger{level: level, writer: writer, module: module}
}

func (l *DefaultLogger) log(level Level, format string, args ...interface{}) {
	if level < l.level {
		return
	}
	entry := Entry{
		Level:   level,
		Time:    time.Now(),
		Module:  l.module,
		Message: fmt.Sprintf(format, args...),
	}
	_ = l.writer.Write(entry)
}

func (l *DefaultLogger) logWithFields(level Level, fields map[string]interface{}, format string, args ...interface{}) {
	if level < l.level {
		return
	}
	entry := Entry{
		Level:   level,
		Time:    time.Now(),
		Module:  l.module,
		Message: fmt.Sprintf(format, args...),
		Fields:  fields,
	}
	_ = l.writer.Write(entry)
}

func (l *DefaultLogger) Debug(format string, args ...interface{}) {
	l.log(DEBUG, format, args...)
}

func (l *DefaultLogger) Info(format string, args ...interface{}) {
	l.log(INFO, format, args...)
}

func (l *DefaultLogger) Warn(format string, args ...interface{}) {
	l.log(WARN, format, args...)
}

func (l *DefaultLogger) Error(format string, args ...interface{}) {
	l.log(ERROR, format, args...)
}

// LogWithFields logs at the given level with structured fields.
func (l *DefaultLogger) LogWithFields(level Level, fields map[string]interface{}, format string, args ...interface{}) {
	l.logWithFields(level, fields, format, args...)
}

// LogEntry implements Logger.LogEntry with level filtering and module override.
func (l *DefaultLogger) LogEntry(entry Entry) {
	if entry.Level < l.level {
		return
	}
	if entry.Module == "" {
		entry.Module = l.module
	}
	if entry.Time.IsZero() {
		entry.Time = time.Now()
	}
	_ = l.writer.Write(entry)
}
