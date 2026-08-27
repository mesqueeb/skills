---
name: apple-documentation
description: Research Apple APIs, platform guidance, Swift, HIG, WWDC sessions, sample code, and Swift-DocC using the Cupertino and Sosumi CLIs. Use for implementation questions or verification involving iOS, macOS, visionOS, watchOS, tvOS, Swift, SwiftUI, UIKit, AppKit, Foundation, RealityKit, or other Apple frameworks.
---

# Apple Documentation

Ground Apple-platform answers in retrieved documentation. Prefer the CLIs; neither needs MCP. Cupertino searches downloaded indexes offline, while Sosumi retrieves live Apple or external Swift-DocC content and requires internet access.

## Choose the source

- Start most lookups with `cupertino search`; its offline indexes cover Apple documentation, sample code, HIG guidance, Swift Evolution, Swift.org, the Swift book, legacy guides, and package documentation.
- Use Sosumi for an online fetch of a currently published Apple page, WWDC transcript, or external Swift-DocC page. Verify claims sensitive to the latest SDK, availability, deprecation, or an exact signature with Sosumi even when Cupertino supplied the page.

## Cupertino

Cupertino is lexical. Search with canonical Apple symbols or terms, correct likely typos, and narrow with `--framework` or `--source` when useful.

```bash
cupertino search "NavigationStack" --source apple-docs --framework swiftui --limit 10 --format markdown
cupertino search "button styles" --source samples --limit 10 --format markdown
cupertino read "apple-docs://swiftui/navigationstack" --format markdown
```

Follow promising result URIs with `cupertino read`. Use `cupertino --help` when ordinary search is insufficient.

## Sosumi

```bash
sosumi search "SwiftData" --json
sosumi fetch "https://developer.apple.com/documentation/swiftui/navigationstack"
sosumi fetch "/videos/play/wwdc2024/10150"
sosumi fetch "https://apple.github.io/swift-argument-parser/documentation/argumentparser"
```

The CLI supports search and fetch with text or JSON output. For a known Apple page when the CLI is unavailable, replace `developer.apple.com` with `sosumi.ai` and fetch the hosted Markdown directly:

```bash
curl -L "https://sosumi.ai/documentation/swiftui/navigationstack"
```

## Evidence and recovery

- Read the specific page before relying on a search excerpt. Verify implementation-driving claims and prefer current APIs for the user's deployment targets.
- Link the canonical Apple, WWDC, Swift proposal, or external DocC page. State what remains unclear when sources do not establish the answer.
- If Cupertino is unavailable, use Sosumi search. If Cupertino results are weak, retry canonical symbol names or a narrower source before switching tools.
- If Sosumi cannot fetch a page, use Cupertino's indexed copy.
- Run `cupertino doctor` only to diagnose Cupertino. Leave the large `cupertino setup` download to the user unless requested.
