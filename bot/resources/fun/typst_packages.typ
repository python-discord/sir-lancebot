// This file is ran to install the allowed packages before the package directory is write-locked.
// It is NOT included into every query's template.
#import "@preview/codly:1.0.0" // code presentation (needs configuration in the document to work)
#import "@preview/cetz:0.3.0" // similar to latex's tikz
#import "@preview/fletcher:0.5.1" as fletcher // drawing diagrams; depends on cetz
#import "@preview/physica:0.9.3" // math and physics
