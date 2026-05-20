package log

import (
	"fmt"
	"io"
	"os"
)

// ConsoleWriter writes log entries to stdout.
type ConsoleWriter struct {
	out io.Writer
}

// NewConsoleWriter creates a ConsoleWriter writing to os.Stdout.
func NewConsoleWriter() *ConsoleWriter {
	return &ConsoleWriter{out: os.Stdout}
}

func (w *ConsoleWriter) Write(entry Entry) error {
	line := fmt.Sprintf("[%s] [%s] [%s] %s",
		entry.Level.String(),
		entry.Time.Format("2006-01-02 15:04:05"),
		entry.Module,
		entry.Message,
	)
	if len(entry.Fields) > 0 {
		line += " " + fmt.Sprint(entry.Fields)
	}
	_, err := fmt.Fprintln(w.out, line)
	return err
}

func (w *ConsoleWriter) Close() error {
	return nil
}
