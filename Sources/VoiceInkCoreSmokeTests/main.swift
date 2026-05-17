import Foundation
import VoiceInkCore

@main
enum VoiceInkCoreSmokeTests {
    static func main() throws {
        try testAppSettingsUseProductionDefaults()
        try testSettingsStoreCreatesDefaultSettingsWhenFileDoesNotExist()
        try testSettingsStorePersistsSettingsAsJson()
        try testHistoryStoreReturnsNewestEntriesFirst()
        try testHistoryStoreTrimsToLimit()
        try testGeminiRequestUsesConfiguredModelAndPrompt()
        try testDefaultHotKeyDescriptorMatchesPythonApp()
        try testDefaultAppIdentityUsesVoiceInk()
        try testDefaultStopModeIsManual()
        try testDefaultFeedbackSettingsAreEnabled()
        try testApiKeyResolverPrefersSecureStore()
        try testApiKeyResolverFallsBackToLegacyEnv()

        print("VoiceInkCoreSmokeTests passed")
    }

    private static func testAppSettingsUseProductionDefaults() throws {
        let settings = AppSettings.default
        try expect(settings.silenceTimeout == 5, "default silence timeout")
        try expect(settings.silenceThreshold == 500, "default silence threshold")
        try expect(settings.historyLimit == 50, "default history limit")
        try expect(settings.autoPasteFinalTranscript, "default auto-paste")
    }

    private static func testSettingsStoreCreatesDefaultSettingsWhenFileDoesNotExist() throws {
        let directory = try TemporaryDirectory()
        let store = SettingsStore(fileURL: directory.url.appending(path: "settings.json"))

        try expect(try store.load() == .default, "settings store missing file default")
    }

    private static func testSettingsStorePersistsSettingsAsJson() throws {
        let directory = try TemporaryDirectory()
        let store = SettingsStore(fileURL: directory.url.appending(path: "settings.json"))
        let settings = AppSettings(
            silenceTimeout: 8,
            silenceThreshold: 650,
            historyLimit: 20,
            autoPasteFinalTranscript: false,
            stopMode: .autoStopAfterSilence,
            silenceStopSeconds: 8,
            soundFeedbackEnabled: false,
            notificationFeedbackEnabled: false
        )

        try store.save(settings)

        try expect(try store.load() == settings, "settings store persistence")
    }

    private static func testHistoryStoreReturnsNewestEntriesFirst() throws {
        let directory = try TemporaryDirectory()
        let store = HistoryStore(fileURL: directory.url.appending(path: "history.json"), limit: 3)

        try store.append(text: "one", duration: 1)
        try store.append(text: "two", duration: 2)

        try expect(try store.load().map(\.text) == ["two", "one"], "history newest first")
    }

    private static func testHistoryStoreTrimsToLimit() throws {
        let directory = try TemporaryDirectory()
        let store = HistoryStore(fileURL: directory.url.appending(path: "history.json"), limit: 2)

        try store.append(text: "one", duration: 1)
        try store.append(text: "two", duration: 2)
        try store.append(text: "three", duration: 3)

        try expect(try store.load().map(\.text) == ["three", "two"], "history limit")
    }

    private static func testGeminiRequestUsesConfiguredModelAndPrompt() throws {
        let audio = Data("audio".utf8)
        let request = try GeminiRequestBuilder(model: "gemini-2.5-flash").makeRequest(
            apiKey: "dummy-api-key",
            audioData: audio
        )

        try expect(
            request.url?.absoluteString.contains("gemini-2.5-flash:generateContent") == true,
            "Gemini model URL"
        )
        try expect(
            request.url?.query?.contains("key=dummy-api-key") == true,
            "Gemini API key query"
        )
        try expect(request.httpMethod == "POST", "Gemini POST")
        try expect(
            request.value(forHTTPHeaderField: "Content-Type") == "application/json",
            "Gemini content type"
        )

        let body = try require(request.httpBody, "Gemini request body")
        let decoded = try JSONSerialization.jsonObject(with: body) as? [String: Any]
        let contents = try require(decoded?["contents"] as? [[String: Any]], "Gemini contents")
        let parts = try require(contents.first?["parts"] as? [[String: Any]], "Gemini parts")

        try expect(parts.description.contains("You are VoiceInk"), "Gemini prompt identity")
        try expect(
            parts.description.contains("Preserve the detected language"), "Gemini language rule")
        try expect(parts.description.contains("Return only the final text"), "Gemini output rule")
        try expect(parts.description.contains(audio.base64EncodedString()), "Gemini audio data")
    }

    private static func testDefaultHotKeyDescriptorMatchesPythonApp() throws {
        let descriptor = HotKeyDescriptor.default

        try expect(descriptor.keyCode == 1, "default hotkey key code")
        try expect(descriptor.modifiers == [.control, .shift], "default hotkey modifiers")
        try expect(descriptor.displayName == "Ctrl+Shift+S", "default hotkey display name")
    }

    private static func testDefaultAppIdentityUsesVoiceInk() throws {
        try expect(AppIdentity.name == "VoiceInk", "app identity name")
        try expect(AppIdentity.bundleIdentifier == "com.enrique.voiceink", "app identity bundle id")
    }

    private static func testDefaultStopModeIsManual() throws {
        let settings = AppSettings.default

        try expect(settings.stopMode == .manual, "default stop mode")
        try expect(settings.silenceStopSeconds == 5, "default silence stop seconds")
    }

    private static func testDefaultFeedbackSettingsAreEnabled() throws {
        let settings = AppSettings.default

        try expect(settings.soundFeedbackEnabled, "default sound feedback")
        try expect(!settings.notificationFeedbackEnabled, "default notification feedback off")
    }

    private static func testApiKeyResolverPrefersSecureStore() throws {
        let directory = try TemporaryDirectory()
        let legacyEnvURL = directory.url.appending(path: ".voice2clip.env")
        try "GOOGLE_API_KEY=legacy-key\n".write(to: legacyEnvURL, atomically: true, encoding: .utf8)

        let secureStore = MemorySecureCredentialStore(values: [.geminiAPIKey: "secure-key"])
        let resolver = APIKeyResolver(secureStore: secureStore, envFileURLs: [legacyEnvURL])

        try expect(try resolver.resolveGeminiAPIKey() == "secure-key", "secure key preference")
    }

    private static func testApiKeyResolverFallsBackToLegacyEnv() throws {
        let directory = try TemporaryDirectory()
        let legacyEnvURL = directory.url.appending(path: ".voice2clip.env")
        try "GOOGLE_API_KEY=legacy-key\n".write(to: legacyEnvURL, atomically: true, encoding: .utf8)

        let secureStore = MemorySecureCredentialStore()
        let resolver = APIKeyResolver(secureStore: secureStore, envFileURLs: [legacyEnvURL])

        try expect(try resolver.resolveGeminiAPIKey() == "legacy-key", "legacy env fallback")
    }

    private static func expect(_ condition: Bool, _ message: String) throws {
        if !condition {
            throw SmokeTestError.failed(message)
        }
    }

    private static func require<T>(_ value: T?, _ message: String) throws -> T {
        guard let value else {
            throw SmokeTestError.failed(message)
        }

        return value
    }
}

private struct TemporaryDirectory {
    let url: URL

    init() throws {
        let base = URL(fileURLWithPath: NSTemporaryDirectory(), isDirectory: true)
        url = base.appending(path: UUID().uuidString, directoryHint: .isDirectory)
        try FileManager.default.createDirectory(at: url, withIntermediateDirectories: true)
    }
}

private enum SmokeTestError: Error, CustomStringConvertible {
    case failed(String)

    var description: String {
        switch self {
        case let .failed(message):
            "Smoke test failed: \(message)"
        }
    }
}
