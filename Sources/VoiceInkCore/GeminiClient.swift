import Foundation

public struct GeminiClient: Sendable {
    private let apiKey: String
    private let requestBuilder: GeminiRequestBuilder
    private let urlSession: URLSession

    public init(
        apiKey: String,
        requestBuilder: GeminiRequestBuilder = GeminiRequestBuilder(),
        urlSession: URLSession = .shared
    ) {
        self.apiKey = apiKey
        self.requestBuilder = requestBuilder
        self.urlSession = urlSession
    }

    public func transcribe(audioFileURL: URL) async throws -> String {
        let audioData = try Data(contentsOf: audioFileURL)
        let request = try requestBuilder.makeRequest(apiKey: apiKey, audioData: audioData)
        let (data, response) = try await urlSession.data(for: request)

        if let httpResponse = response as? HTTPURLResponse,
            !(200..<300).contains(httpResponse.statusCode)
        {
            let detail = String(data: data, encoding: .utf8) ?? "HTTP \(httpResponse.statusCode)"
            throw GeminiClientError.requestFailed(detail)
        }

        let decoded: GeminiResponse
        do {
            decoded = try JSONDecoder().decode(GeminiResponse.self, from: data)
        } catch {
            let rawResponse = String(data: data, encoding: .utf8) ?? "<non-UTF8 response>"
            throw GeminiClientError.unreadableResponse(rawResponse)
        }

        if let error = decoded.error {
            throw GeminiClientError.requestFailed(error.message)
        }

        guard let candidates = decoded.candidates, !candidates.isEmpty else {
            let rawResponse = String(data: data, encoding: .utf8) ?? "<non-UTF8 response>"
            throw GeminiClientError.missingCandidates(rawResponse)
        }

        let text =
            candidates
            .flatMap(\.content.parts)
            .compactMap(\.text)
            .joined(separator: "\n")
            .trimmingCharacters(in: .whitespacesAndNewlines)

        if text.isEmpty {
            throw GeminiClientError.emptyResponse
        }

        return text
    }
}

public enum GeminiClientError: Error, LocalizedError {
    case requestFailed(String)
    case emptyResponse
    case missingCandidates(String)
    case unreadableResponse(String)

    public var errorDescription: String? {
        switch self {
        case let .requestFailed(detail):
            "Gemini request failed: \(detail)"
        case .emptyResponse:
            "Gemini returned an empty response."
        case let .missingCandidates(rawResponse):
            "Gemini returned no transcript candidates: \(rawResponse)"
        case let .unreadableResponse(rawResponse):
            "Gemini returned an unreadable response: \(rawResponse)"
        }
    }
}

private struct GeminiResponse: Decodable {
    let candidates: [Candidate]?
    let error: APIError?

    struct APIError: Decodable {
        let message: String
    }

    struct Candidate: Decodable {
        let content: Content
    }

    struct Content: Decodable {
        let parts: [Part]
    }

    struct Part: Decodable {
        let text: String?
    }
}
