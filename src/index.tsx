#!/usr/bin/env bun
import { render } from "ink"
import { App } from "./tui/App.js"

if (!process.stdin.isTTY) {
  console.error("Error: botler requires an interactive terminal")
  process.exit(1)
}

render(<App />)
