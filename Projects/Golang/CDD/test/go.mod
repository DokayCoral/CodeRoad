module cdd/test

go 1.26.3

require (
	cdd/src v0.0.0
	github.com/go-resty/resty/v2 v2.17.2
)

require golang.org/x/net v0.51.0 // indirect

replace cdd/src => ../src
