import AVFoundation
import AppKit
import VoiceInkCore

@MainActor
final class VoiceInkApp: NSObject, NSApplicationDelegate {
    private let statusItem = NSStatusBar.system.statusItem(withLength: NSStatusItem.variableLength)
    private let recorder = NativeAudioRecorder()
    private let autoPasteController = AutoPasteController()
    private let feedbackController = FeedbackController()
    private let credentialStore = KeychainCredentialStore()
    private let settingsStore = SettingsStore()
    private var globalHotKey: GlobalHotKey?
    private var historyStore = HistoryStore()
    private var settings = AppSettings.default
    private var recordItem: NSMenuItem?
    private var latestItem: NSMenuItem?
    private var stateItem: NSMenuItem?
    private var stopModeItem: NSMenuItem?
    private var settingsWindowController: SettingsWindowController?
    private var startedAt: Date?

    func applicationDidFinishLaunching(_ notification: Notification) {
        NSApp.setActivationPolicy(.accessory)
        configureStatusItem()
        configureStores()
        migrateLegacyAPIKeyIfNeeded()
        configureHotKey()
        refreshMenu(state: "Ready")
    }

    private func configureStatusItem() {
        statusItem.button?.image = statusImage(systemName: "waveform.circle")
        statusItem.button?.imagePosition = .imageOnly
        statusItem.button?.toolTip = AppIdentity.displayName

        let menu = NSMenu()
        let stateItem = NSMenuItem(title: "Ready", action: nil, keyEquivalent: "")
        let stopModeItem = NSMenuItem(title: "Stop: Manual", action: nil, keyEquivalent: "")
        let feedbackItem = NSMenuItem(title: "Feedback: Sound", action: nil, keyEquivalent: "")
        let recordItem = NSMenuItem(
            title: "Start Recording",
            action: #selector(toggleRecording),
            keyEquivalent: "r"
        )
        let latestItem = NSMenuItem(title: "No transcription yet", action: nil, keyEquivalent: "")
        let requestAccessibilityItem = NSMenuItem(
            title: "Request Paste Permission",
            action: #selector(requestPastePermission),
            keyEquivalent: ""
        )
        let testPasteItem = NSMenuItem(
            title: "Test Paste Permission",
            action: #selector(testPastePermission),
            keyEquivalent: ""
        )
        let settingsItem = NSMenuItem(
            title: "Settings...",
            action: #selector(openSettings),
            keyEquivalent: ","
        )
        let openSupportItem = NSMenuItem(
            title: "Open App Support",
            action: #selector(openAppSupport),
            keyEquivalent: ""
        )
        let quitItem = NSMenuItem(
            title: "Quit VoiceInk",
            action: #selector(quit),
            keyEquivalent: "q"
        )

        recordItem.target = self
        requestAccessibilityItem.target = self
        testPasteItem.target = self
        settingsItem.target = self
        openSupportItem.target = self
        quitItem.target = self
        latestItem.isEnabled = false
        stateItem.isEnabled = false
        stopModeItem.isEnabled = false
        feedbackItem.isEnabled = false

        menu.addItem(stateItem)
        menu.addItem(stopModeItem)
        menu.addItem(feedbackItem)
        menu.addItem(.separator())
        menu.addItem(recordItem)
        menu.addItem(latestItem)
        menu.addItem(.separator())
        menu.addItem(requestAccessibilityItem)
        menu.addItem(testPasteItem)
        menu.addItem(settingsItem)
        menu.addItem(openSupportItem)
        menu.addItem(quitItem)
        statusItem.menu = menu

        self.stateItem = stateItem
        self.stopModeItem = stopModeItem
        self.recordItem = recordItem
        self.latestItem = latestItem
    }

    private func configureStores() {
        settings = (try? settingsStore.load()) ?? .default
        historyStore = HistoryStore(limit: settings.historyLimit)
        feedbackController.configure(settings: settings)
    }

    private func migrateLegacyAPIKeyIfNeeded() {
        guard (try? credentialStore.read(.geminiAPIKey)) == nil else {
            return
        }

        let resolver = APIKeyResolver(secureStore: MemorySecureCredentialStore())
        guard let apiKey = try? resolver.resolveGeminiAPIKey(), !apiKey.isEmpty else {
            return
        }

        try? credentialStore.save(apiKey, for: .geminiAPIKey)
    }

    private func configureHotKey() {
        let hotKey = GlobalHotKey { [weak self] in
            self?.toggleRecording()
        }

        do {
            try hotKey.register()
            globalHotKey = hotKey
            stateItem?.title = "Ready - \(hotKey.displayName)"
        } catch {
            globalHotKey = nil
            stateItem?.title = "Hotkey failed: \(error.localizedDescription)"
        }
    }

    private func refreshMenu(state: String) {
        stateItem?.title = state
        stopModeItem?.title = "Stop: \(settings.stopMode.displayName)"
        recordItem?.title = recorder.isRecording ? "Stop and Transcribe" : "Start Recording"
        statusItem.button?.image = statusImage(
            systemName: recorder.isRecording ? "record.circle.fill" : "waveform.circle"
        )

        if let latest = try? historyStore.load().first {
            latestItem?.title = "Last: \(latest.text.prefix(64))"
        }
    }

    private func statusImage(systemName: String) -> NSImage? {
        let image = NSImage(
            systemSymbolName: systemName, accessibilityDescription: AppIdentity.name)
        image?.isTemplate = true
        return image
    }

    @objc private func toggleRecording() {
        if recorder.isRecording {
            stopAndTranscribe()
        } else {
            startRecording()
        }
    }

    private func startRecording() {
        AVCaptureDevice.requestAccess(for: .audio) { [weak self] granted in
            DispatchQueue.main.async {
                guard let self else { return }
                guard granted else {
                    self.refreshMenu(state: "Microphone permission needed")
                    return
                }

                do {
                    self.startedAt = Date()
                    try self.recorder.start(url: AppPaths.recordingURL)
                    self.feedbackController.recordingStarted()
                    let suffix =
                        self.settings.stopMode == .manual
                        ? "Ctrl+Shift+S to stop"
                        : "auto-stop after \(self.settings.silenceStopSeconds)s silence"
                    self.refreshMenu(state: "Recording... \(suffix)")
                } catch {
                    self.refreshMenu(state: "Recording failed: \(error.localizedDescription)")
                }
            }
        }
    }

    private func stopAndTranscribe() {
        let audioURL = recorder.stop()
        let duration = startedAt.map { Date().timeIntervalSince($0) } ?? 0
        feedbackController.recordingStopped()
        refreshMenu(state: "Transcribing...")

        Task { [audioURL, duration] in
            do {
                let resolver = APIKeyResolver(secureStore: credentialStore)
                let apiKey = try resolver.resolveGeminiAPIKey()
                let text = try await GeminiClient(apiKey: apiKey).transcribe(audioFileURL: audioURL)
                try historyStore.append(text: text, duration: duration)

                copyToClipboard(text)
                latestItem?.title = "Last: \(text.prefix(64))"
                feedbackController.transcriptionSucceeded()

                if settings.autoPasteFinalTranscript {
                    DispatchQueue.main.asyncAfter(deadline: .now() + 0.15) {
                        let didPaste = self.autoPasteController.pasteClipboardIntoFocusedApp()
                        self.refreshMenu(
                            state: didPaste
                                ? "Pasted into focused app"
                                : "Copied. Paste permission needed"
                        )
                    }
                } else {
                    refreshMenu(state: "Copied to clipboard")
                }
            } catch {
                let message = error.localizedDescription
                feedbackController.transcriptionFailed(message)
                refreshMenu(state: "Error: \(message)")
            }
        }
    }

    private func copyToClipboard(_ text: String) {
        NSPasteboard.general.clearContents()
        NSPasteboard.general.setString(text, forType: .string)
    }

    @objc private func openAppSupport() {
        try? FileManager.default.createDirectory(
            at: AppPaths.appSupportDirectory,
            withIntermediateDirectories: true
        )
        NSWorkspace.shared.open(AppPaths.appSupportDirectory)
    }

    @objc private func requestPastePermission() {
        autoPasteController.requestPermissionAndOpenSettings()
        refreshMenu(
            state: autoPasteController.isTrusted
                ? "Paste permission enabled"
                : "Enable Accessibility for auto-paste"
        )
    }

    @objc private func testPastePermission() {
        NSPasteboard.general.clearContents()
        NSPasteboard.general.setString("VoiceInk paste test", forType: .string)

        let didPaste = autoPasteController.pasteClipboardIntoFocusedApp()
        refreshMenu(
            state: didPaste
                ? "Paste test sent"
                : "Paste test copied only"
        )
    }

    @objc private func openSettings() {
        let controller = SettingsWindowController(
            credentialStore: credentialStore,
            autoPasteController: autoPasteController
        )
        settingsWindowController = controller
        controller.showWindow(nil)
        NSApp.activate(ignoringOtherApps: true)
    }

    @objc private func quit() {
        globalHotKey?.unregister()
        recorder.cancel()
        NSApp.terminate(nil)
    }
}

@MainActor
final class NativeAudioRecorder: NSObject, AVAudioRecorderDelegate {
    private var recorder: AVAudioRecorder?

    var isRecording: Bool {
        recorder?.isRecording == true
    }

    func start(url: URL) throws {
        try? FileManager.default.removeItem(at: url)
        let settings: [String: Any] = [
            AVFormatIDKey: Int(kAudioFormatLinearPCM),
            AVSampleRateKey: 44_100,
            AVNumberOfChannelsKey: 1,
            AVLinearPCMBitDepthKey: 16,
            AVLinearPCMIsFloatKey: false,
            AVLinearPCMIsBigEndianKey: false,
        ]

        let recorder = try AVAudioRecorder(url: url, settings: settings)
        recorder.delegate = self
        recorder.prepareToRecord()
        recorder.record()
        self.recorder = recorder
    }

    func stop() -> URL {
        let url = recorder?.url ?? AppPaths.recordingURL
        recorder?.stop()
        recorder = nil
        return url
    }

    func cancel() {
        recorder?.stop()
        recorder = nil
    }
}
