package log

import (
	"bufio"
	"encoding/json"
	"os"
	"path/filepath"
	"sync"
)

// FileWriter writes log entries as JSON lines to a file.
type FileWriter struct {
	mu     sync.Mutex
	file   *os.File
	writer *bufio.Writer
}

// NewFileWriter creates a FileWriter. Creates parent directories if needed.
func NewFileWriter(path string) (*FileWriter, error) {
	dir := filepath.Dir(path)
	if err := os.MkdirAll(dir, 0755); err != nil {
		return nil, err
	}

	file, err := os.OpenFile(path, os.O_CREATE|os.O_WRONLY|os.O_APPEND, 0644)
	if err != nil {
		return nil, err
	}

	return &FileWriter{
		file:   file,
		writer: bufio.NewWriter(file),
	}, nil
}

func (w *FileWriter) Write(entry Entry) error {
	w.mu.Lock()
	defer w.mu.Unlock()

	data, err := json.Marshal(entry)
	if err != nil {
		return err
	}
	_, err = w.writer.Write(append(data, '\n'))
	if err != nil {
		return err
	}
	return w.writer.Flush()
}

func (w *FileWriter) Close() error {
	w.mu.Lock()
	defer w.mu.Unlock()

	if err := w.writer.Flush(); err != nil {
		return err
	}
	return w.file.Close()
}
