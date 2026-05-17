import Foundation

public struct HistoryEntry: Codable, Equatable, Identifiable, Sendable {
    public let id: UUID
    public let text: String
    public let duration: TimeInterval
    public let createdAt: Date

    public init(
        id: UUID = UUID(),
        text: String,
        duration: TimeInterval,
        createdAt: Date = Date()
    ) {
        self.id = id
        self.text = text
        self.duration = duration
        self.createdAt = createdAt
    }
}

public struct HistoryStore: Sendable {
    private let fileURL: URL
    private let limit: Int

    public init(fileURL: URL = AppPaths.historyURL, limit: Int = AppSettings.default.historyLimit) {
        self.fileURL = fileURL
        self.limit = limit
    }

    public func load() throws -> [HistoryEntry] {
        guard FileManager.default.fileExists(atPath: fileURL.path) else {
            return []
        }

        let data = try Data(contentsOf: fileURL)
        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .iso8601
        return try decoder.decode([HistoryEntry].self, from: data)
    }

    public func append(text: String, duration: TimeInterval) throws {
        let entry = HistoryEntry(text: text, duration: duration)
        let trimmed = Array(([entry] + (try load())).prefix(limit))

        try FileManager.default.createDirectory(
            at: fileURL.deletingLastPathComponent(),
            withIntermediateDirectories: true
        )

        let encoder = JSONEncoder()
        encoder.outputFormatting = [.prettyPrinted, .sortedKeys]
        encoder.dateEncodingStrategy = .iso8601
        let data = try encoder.encode(trimmed)
        try data.write(to: fileURL, options: .atomic)
    }
}
