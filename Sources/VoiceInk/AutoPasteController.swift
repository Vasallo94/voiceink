import AppKit
import ApplicationServices
import Foundation

@MainActor
final class AutoPasteController {
    var isTrusted: Bool {
        AXIsProcessTrusted()
    }

    func requestPermissionPrompt() {
        let options =
            [
                "AXTrustedCheckOptionPrompt": true
            ] as CFDictionary
        AXIsProcessTrustedWithOptions(options)
    }

    func openAccessibilitySettings() {
        let urls = [
            "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility",
            "x-apple.systempreferences:com.apple.preference.universalaccess",
        ]

        for urlString in urls {
            guard let url = URL(string: urlString), NSWorkspace.shared.open(url) else {
                continue
            }
            break
        }
    }

    func requestPermissionAndOpenSettings() {
        requestPermissionPrompt()
        if !isTrusted {
            openAccessibilitySettings()
        }
    }

    func pasteClipboardIntoFocusedApp() -> Bool {
        paste(into: nil)
    }

    /// Activates `targetApp` (if provided) then sends Cmd+V.
    /// Capturing the target before the async transcription ensures the paste
    /// reaches the right app even if the user opened the VoiceInk menu in between.
    func paste(into targetApp: NSRunningApplication?) -> Bool {
        guard isTrusted else {
            return false
        }

        targetApp?.activate(options: .activateIgnoringOtherApps)

        let source = CGEventSource(stateID: .combinedSessionState)
        let keyCodeForV = CGKeyCode(9)
        let keyDown = CGEvent(keyboardEventSource: source, virtualKey: keyCodeForV, keyDown: true)
        let keyUp = CGEvent(keyboardEventSource: source, virtualKey: keyCodeForV, keyDown: false)

        keyDown?.flags = .maskCommand
        keyUp?.flags = .maskCommand
        keyDown?.post(tap: .cghidEventTap)
        keyUp?.post(tap: .cghidEventTap)

        return keyDown != nil && keyUp != nil
    }
}
