import AppKit
import Foundation
import UserNotifications
import VoiceInkCore

@MainActor
final class FeedbackController {
    private var settings = AppSettings.default

    func configure(settings: AppSettings) {
        self.settings = settings
        if settings.notificationFeedbackEnabled {
            UNUserNotificationCenter.current().requestAuthorization(options: [.alert, .sound]) {
                _, _ in
            }
        }
    }

    func recordingStarted() {
        playSound(named: "Tink")
    }

    func recordingStopped() {
        playSound(named: "Pop")
    }

    func transcriptionSucceeded() {
        playSound(named: "Glass")
        notify(title: "VoiceInk", body: "Transcription pasted")
    }

    func transcriptionFailed(_ message: String) {
        playSound(named: "Basso")
        notify(title: "VoiceInk error", body: message)
    }

    private func playSound(named name: String) {
        guard settings.soundFeedbackEnabled else {
            return
        }

        NSSound(named: NSSound.Name(name))?.play()
    }

    private func notify(title: String, body: String) {
        guard settings.notificationFeedbackEnabled else {
            return
        }

        let content = UNMutableNotificationContent()
        content.title = title
        content.body = body
        content.sound = nil

        let request = UNNotificationRequest(
            identifier: UUID().uuidString,
            content: content,
            trigger: nil
        )
        UNUserNotificationCenter.current().add(request)
    }
}
