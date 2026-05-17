import AppKit
import VoiceInkCore

@MainActor
final class SettingsWindowController: NSWindowController {
    private let credentialStore: any SecureCredentialStore
    private let autoPasteController: AutoPasteController
    private let geminiKeyField = NSSecureTextField()
    private let statusLabel = NSTextField(labelWithString: "")

    init(credentialStore: any SecureCredentialStore, autoPasteController: AutoPasteController) {
        self.credentialStore = credentialStore
        self.autoPasteController = autoPasteController

        let window = NSWindow(
            contentRect: NSRect(x: 0, y: 0, width: 460, height: 230),
            styleMask: [.titled, .closable],
            backing: .buffered,
            defer: false
        )
        window.title = "VoiceInk Settings"
        window.center()

        super.init(window: window)
        configureContent()
        reload()
    }

    @available(*, unavailable)
    required init?(coder: NSCoder) {
        nil
    }

    private func configureContent() {
        guard let contentView = window?.contentView else {
            return
        }

        let titleLabel = NSTextField(labelWithString: "API Keys")
        titleLabel.font = .boldSystemFont(ofSize: 16)

        let geminiLabel = NSTextField(labelWithString: "Gemini API Key")
        geminiKeyField.placeholderString = "Google AI Studio key"
        geminiKeyField.usesSingleLineMode = true

        let saveButton = NSButton(
            title: "Save",
            target: self,
            action: #selector(save)
        )
        saveButton.bezelStyle = .rounded

        let requestPasteButton = NSButton(
            title: "Request Paste Permission",
            target: self,
            action: #selector(requestPastePermission)
        )
        requestPasteButton.bezelStyle = .rounded

        let testPasteButton = NSButton(
            title: "Test Paste Permission",
            target: self,
            action: #selector(testPastePermission)
        )
        testPasteButton.bezelStyle = .rounded

        statusLabel.lineBreakMode = .byWordWrapping
        statusLabel.maximumNumberOfLines = 3

        let stack = NSStackView(views: [
            titleLabel,
            geminiLabel,
            geminiKeyField,
            saveButton,
            requestPasteButton,
            testPasteButton,
            statusLabel,
        ])
        stack.orientation = .vertical
        stack.alignment = .leading
        stack.spacing = 10
        stack.translatesAutoresizingMaskIntoConstraints = false

        contentView.addSubview(stack)
        NSLayoutConstraint.activate([
            stack.leadingAnchor.constraint(equalTo: contentView.leadingAnchor, constant: 20),
            stack.trailingAnchor.constraint(equalTo: contentView.trailingAnchor, constant: -20),
            stack.topAnchor.constraint(equalTo: contentView.topAnchor, constant: 20),
            geminiKeyField.widthAnchor.constraint(equalTo: stack.widthAnchor),
        ])
    }

    private func reload() {
        if let geminiKey = try? credentialStore.read(.geminiAPIKey), !geminiKey.isEmpty {
            geminiKeyField.stringValue = geminiKey
        }
        updateStatus(
            "Gemini: \(hasGeminiKey ? "configured" : "missing") · Accessibility: \(autoPasteController.isTrusted ? "enabled" : "missing")"
        )
    }

    private var hasGeminiKey: Bool {
        ((try? credentialStore.read(.geminiAPIKey)) ?? nil)?.isEmpty == false
    }

    private func updateStatus(_ message: String) {
        statusLabel.stringValue = message
    }

    @objc private func save() {
        do {
            let value = geminiKeyField.stringValue.trimmingCharacters(in: .whitespacesAndNewlines)
            if value.isEmpty {
                try credentialStore.delete(.geminiAPIKey)
            } else {
                try credentialStore.save(value, for: .geminiAPIKey)
            }
            updateStatus("Saved. Gemini: \(hasGeminiKey ? "configured" : "missing")")
        } catch {
            updateStatus("Save failed: \(error.localizedDescription)")
        }
    }

    @objc private func requestPastePermission() {
        autoPasteController.requestPermissionAndOpenSettings()
        updateStatus("Accessibility: \(autoPasteController.isTrusted ? "enabled" : "missing")")
    }

    @objc private func testPastePermission() {
        NSPasteboard.general.clearContents()
        NSPasteboard.general.setString("VoiceInk paste test", forType: .string)

        let didPaste = autoPasteController.pasteClipboardIntoFocusedApp()
        updateStatus(
            didPaste
                ? "Paste test sent. Check the focused text field."
                : "Paste test copied only. Enable Accessibility for /Applications/VoiceInk.app."
        )
    }
}
