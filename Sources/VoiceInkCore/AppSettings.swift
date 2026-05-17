import Foundation

public struct AppSettings: Codable, Equatable, Sendable {
    public let silenceTimeout: Int
    public let silenceThreshold: Int
    public let historyLimit: Int
    public let autoPasteFinalTranscript: Bool
    public let stopMode: StopMode
    public let silenceStopSeconds: Int
    public let soundFeedbackEnabled: Bool
    public let notificationFeedbackEnabled: Bool

    public static let `default` = AppSettings(
        silenceTimeout: 5,
        silenceThreshold: 500,
        historyLimit: 50,
        autoPasteFinalTranscript: true,
        stopMode: .manual,
        silenceStopSeconds: 5,
        soundFeedbackEnabled: true,
        notificationFeedbackEnabled: false
    )

    public init(
        silenceTimeout: Int,
        silenceThreshold: Int,
        historyLimit: Int,
        autoPasteFinalTranscript: Bool,
        stopMode: StopMode,
        silenceStopSeconds: Int,
        soundFeedbackEnabled: Bool,
        notificationFeedbackEnabled: Bool
    ) {
        self.silenceTimeout = silenceTimeout
        self.silenceThreshold = silenceThreshold
        self.historyLimit = historyLimit
        self.autoPasteFinalTranscript = autoPasteFinalTranscript
        self.stopMode = stopMode
        self.silenceStopSeconds = silenceStopSeconds
        self.soundFeedbackEnabled = soundFeedbackEnabled
        self.notificationFeedbackEnabled = notificationFeedbackEnabled
    }

    public init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        silenceTimeout = try container.decode(Int.self, forKey: .silenceTimeout)
        silenceThreshold = try container.decode(Int.self, forKey: .silenceThreshold)
        historyLimit = try container.decode(Int.self, forKey: .historyLimit)
        autoPasteFinalTranscript =
            try container.decodeIfPresent(
                Bool.self,
                forKey: .autoPasteFinalTranscript
            ) ?? true
        stopMode = try container.decodeIfPresent(StopMode.self, forKey: .stopMode) ?? .manual
        silenceStopSeconds =
            try container.decodeIfPresent(
                Int.self,
                forKey: .silenceStopSeconds
            ) ?? 5
        soundFeedbackEnabled =
            try container.decodeIfPresent(
                Bool.self,
                forKey: .soundFeedbackEnabled
            ) ?? true
        notificationFeedbackEnabled =
            try container.decodeIfPresent(
                Bool.self,
                forKey: .notificationFeedbackEnabled
            ) ?? false
    }
}

public enum StopMode: String, Codable, Equatable, Sendable {
    case manual
    case autoStopAfterSilence

    public var displayName: String {
        switch self {
        case .manual:
            "Manual"
        case .autoStopAfterSilence:
            "Auto-stop after silence"
        }
    }
}

public struct SettingsStore: Sendable {
    private let fileURL: URL

    public init(fileURL: URL = AppPaths.settingsURL) {
        self.fileURL = fileURL
    }

    public func load() throws -> AppSettings {
        guard FileManager.default.fileExists(atPath: fileURL.path) else {
            return .default
        }

        let data = try Data(contentsOf: fileURL)
        return try JSONDecoder().decode(AppSettings.self, from: data)
    }

    public func save(_ settings: AppSettings) throws {
        try FileManager.default.createDirectory(
            at: fileURL.deletingLastPathComponent(),
            withIntermediateDirectories: true
        )
        let encoder = JSONEncoder()
        encoder.outputFormatting = [.prettyPrinted, .sortedKeys]
        let data = try encoder.encode(settings)
        try data.write(to: fileURL, options: .atomic)
    }
}
