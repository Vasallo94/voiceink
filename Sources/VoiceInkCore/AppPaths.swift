import Foundation

public enum AppPaths {
    public static let appSupportDirectory: URL = {
        let base =
            FileManager.default.urls(
                for: .applicationSupportDirectory,
                in: .userDomainMask
            ).first
            ?? URL(fileURLWithPath: NSHomeDirectory()).appending(
                path: "Library/Application Support")

        return base.appending(path: AppIdentity.name, directoryHint: .isDirectory)
    }()

    public static let settingsURL = appSupportDirectory.appending(path: "settings.json")
    public static let historyURL = appSupportDirectory.appending(path: "history.json")
    public static let recordingURL = FileManager.default.temporaryDirectory.appending(
        path: "voiceink-recording.wav"
    )
}
