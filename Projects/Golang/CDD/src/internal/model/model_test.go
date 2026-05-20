package model

import "testing"

func TestRideStatusConstants(t *testing.T) {
	tests := []struct {
		name     string
		constant int
		expected int
	}{
		{"Pending", RideStatusPending, 0},
		{"Matched", RideStatusMatched, 1},
		{"Accepted", RideStatusAccepted, 2},
		{"Arrived", RideStatusArrived, 3},
		{"Started", RideStatusStarted, 4},
		{"Completed", RideStatusCompleted, 5},
		{"Cancelled", RideStatusCancelled, 6},
	}

	for _, tc := range tests {
		if tc.constant != tc.expected {
			t.Errorf("RideStatus%s: expected %d, got %d", tc.name, tc.expected, tc.constant)
		}
	}
}

func TestDriverStatusConstants(t *testing.T) {
	if DriverStatusOffline != 0 {
		t.Errorf("Offline: expected 0, got %d", DriverStatusOffline)
	}
	if DriverStatusOnline != 1 {
		t.Errorf("Online: expected 1, got %d", DriverStatusOnline)
	}
	if DriverStatusBusy != 2 {
		t.Errorf("Busy: expected 2, got %d", DriverStatusBusy)
	}
}

func TestRideStatusValuesUnique(t *testing.T) {
	seen := make(map[int]bool)
	all := []int{
		RideStatusPending, RideStatusMatched, RideStatusAccepted,
		RideStatusArrived, RideStatusStarted, RideStatusCompleted, RideStatusCancelled,
	}
	for _, s := range all {
		if seen[s] {
			t.Errorf("duplicate status value: %d", s)
		}
		seen[s] = true
	}
}
