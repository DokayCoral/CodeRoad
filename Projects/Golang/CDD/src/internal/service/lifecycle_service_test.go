package service

import (
	"testing"

	"cdd/src/internal/model"
)

func TestCanTransition_ValidPaths(t *testing.T) {
	svc := &LifecycleService{}

	tests := []struct {
		from, to int
		valid    bool
	}{
		{model.RideStatusPending, model.RideStatusMatched, true},
		{model.RideStatusPending, model.RideStatusCancelled, true},
		{model.RideStatusMatched, model.RideStatusAccepted, true},
		{model.RideStatusMatched, model.RideStatusCancelled, true},
		{model.RideStatusAccepted, model.RideStatusArrived, true},
		{model.RideStatusArrived, model.RideStatusStarted, true},
		{model.RideStatusStarted, model.RideStatusCompleted, true},
	}

	for _, tc := range tests {
		if got := svc.canTransition(tc.from, tc.to); got != tc.valid {
			t.Errorf("transition %d→%d: expected %v, got %v", tc.from, tc.to, tc.valid, got)
		}
	}
}

func TestCanTransition_InvalidPaths(t *testing.T) {
	svc := &LifecycleService{}

	invalid := []struct{ from, to int }{
		{model.RideStatusPending, model.RideStatusAccepted},    // skip Matched
		{model.RideStatusPending, model.RideStatusStarted},     // skip all
		{model.RideStatusStarted, model.RideStatusCancelled},   // can't cancel once started
		{model.RideStatusCompleted, model.RideStatusStarted},   // can't go back
		{model.RideStatusCancelled, model.RideStatusPending},   // can't uncancel
		{model.RideStatusMatched, model.RideStatusCompleted},   // skip steps
	}

	for _, tc := range invalid {
		if got := svc.canTransition(tc.from, tc.to); got {
			t.Errorf("transition %d→%d: expected invalid, but was allowed", tc.from, tc.to)
		}
	}
}

func TestValidTransitions_Coverage(t *testing.T) {
	// Ensure Completed and Cancelled have no outgoing edges
	if allowed, ok := validTransitions[model.RideStatusCompleted]; ok {
		t.Errorf("Completed should have no transitions, got %v", allowed)
	}
	if allowed, ok := validTransitions[model.RideStatusCancelled]; ok {
		t.Errorf("Cancelled should have no transitions, got %v", allowed)
	}
}
