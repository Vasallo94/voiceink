import Foundation

public enum CredentialKey: String, Sendable {
    case geminiAPIKey = "gemini_api_key"
    case openAIAPIKey = "openai_api_key"
}

public protocol SecureCredentialStore: Sendable {
    func read(_ key: CredentialKey) throws -> String?
    func save(_ value: String, for key: CredentialKey) throws
    func delete(_ key: CredentialKey) throws
}

public final class MemorySecureCredentialStore: SecureCredentialStore, @unchecked Sendable {
    private var values: [CredentialKey: String]

    public init(values: [CredentialKey: String] = [:]) {
        self.values = values
    }

    public func read(_ key: CredentialKey) throws -> String? {
        values[key]
    }

    public func save(_ value: String, for key: CredentialKey) throws {
        values[key] = value
    }

    public func delete(_ key: CredentialKey) throws {
        values.removeValue(forKey: key)
    }
}

public struct APIKeyResolver: Sendable {
    private let secureStore: any SecureCredentialStore
    private let envFileURLs: [URL]

    public init(
        secureStore: any SecureCredentialStore, envFileURLs: [URL] = Self.defaultEnvFileURLs
    ) {
        self.secureStore = secureStore
        self.envFileURLs = envFileURLs
    }

    /// Resolves the path to a service account JSON file.
    /// Resolution order:
    ///   1. `GOOGLE_SERVICE_ACCOUNT_PATH` in `~/.voiceink.env`
    ///   2. `GOOGLE_APPLICATION_CREDENTIALS` environment variable (standard GCP convention)
    ///   3. `~/.voiceink-sa.json` (drop-in default location)
    public func resolveServiceAccountURL() -> URL? {
        if let path = readEnvValue(named: "GOOGLE_SERVICE_ACCOUNT_PATH"), !path.isEmpty {
            return URL(fileURLWithPath: path)
        }
        if let path = ProcessInfo.processInfo.environment["GOOGLE_APPLICATION_CREDENTIALS"],
            !path.isEmpty
        {
            return URL(fileURLWithPath: path)
        }
        let defaultURL = URL(fileURLWithPath: NSHomeDirectory()).appending(path: ".voiceink-sa.json")
        return FileManager.default.fileExists(atPath: defaultURL.path) ? defaultURL : nil
    }

    public func resolveGeminiAPIKey() throws -> String {
        if let secureValue = try secureStore.read(.geminiAPIKey), !secureValue.isEmpty {
            return secureValue
        }

        if let envValue = readEnvValue(named: "GOOGLE_API_KEY"), !envValue.isEmpty {
            return envValue
        }

        throw APIKeyResolutionError.missingGeminiAPIKey
    }

    public static var defaultEnvFileURLs: [URL] {
        let homeURL = URL(fileURLWithPath: NSHomeDirectory())
        return [
            homeURL.appending(path: ".voiceink.env"),
            homeURL.appending(path: ".voice2clip.env"),
        ]
    }

    private func readEnvValue(named name: String) -> String? {
        for envFileURL in envFileURLs {
            guard let contents = try? String(contentsOf: envFileURL, encoding: .utf8) else {
                continue
            }

            for line in contents.split(separator: "\n") {
                let parts = line.split(separator: "=", maxSplits: 1).map(String.init)
                if parts.first == name {
                    return parts.last
                }
            }
        }

        return nil
    }
}

public enum APIKeyResolutionError: Error, LocalizedError {
    case missingGeminiAPIKey

    public var errorDescription: String? {
        switch self {
        case .missingGeminiAPIKey:
            "Gemini API key is missing. Add it in VoiceInk Settings."
        }
    }
}
