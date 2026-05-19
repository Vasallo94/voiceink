import Foundation

public let transcriptionPrompt = """
    You are VoiceInk, a precise speech-to-text cleanup engine for a macOS dictation app.

    Task:
    Transcribe the provided audio into polished text that is ready to paste into the user's active document, chat, email, note, or code-adjacent workflow.

    Language:
    - Preserve the detected language of the speaker.
    - Do not translate unless the speaker explicitly asks for translation.
    - Preserve intentional code-switching between languages.

    Cleanup rules:
    - Remove filler words, false starts, repeated fragments, and hesitation markers when they do not add meaning.
    - Keep the speaker's intent, terminology, names, numbers, and technical vocabulary.
    - Fix obvious punctuation, casing, spacing, and sentence boundaries.
    - Keep the result natural and concise, but do not summarize or omit meaningful content.
    - If the speaker dictates punctuation, formatting, bullets, headings, numbered lists, or line breaks, apply those instructions.
    - If the speaker asks for a format such as an email, Slack message, task list, commit message, command, or code comment, output that format directly.
    - If the audio is empty, silent, or unintelligible, return exactly: No speech detected.

    Output:
    - Return only the final text to paste.
    - Do not mention that this is a transcription.
    - Do not explain your edits.
    - Do not answer the speaker's content as an assistant.
    - Do not wrap the output in quotes or Markdown fences unless the speaker explicitly requested that format.
    """

public struct GeminiRequestBuilder: Sendable {
    private let model: String
    private let prompt: String
    private let vertexProject: String?
    private let vertexLocation: String

    /// AI Studio endpoint (API key auth).
    public init(model: String = "gemini-2.5-flash", prompt: String = transcriptionPrompt) {
        self.model = model
        self.prompt = prompt
        self.vertexProject = nil
        self.vertexLocation = "europe-west1"
    }

    /// Vertex AI endpoint (service account / bearer auth).
    public init(
        model: String = "gemini-2.5-flash",
        vertexProject: String,
        vertexLocation: String = "europe-west1",
        prompt: String = transcriptionPrompt
    ) {
        self.model = model
        self.prompt = prompt
        self.vertexProject = vertexProject
        self.vertexLocation = vertexLocation
    }

    public func makeRequest(auth: GeminiAuth, audioData: Data) throws -> URLRequest {
        var components = URLComponents()
        components.scheme = "https"

        if let project = vertexProject, case .bearer = auth {
            // Vertex AI: https://{location}-aiplatform.googleapis.com/v1/projects/{project}/...
            components.host = "\(vertexLocation)-aiplatform.googleapis.com"
            components.path =
                "/v1/projects/\(project)/locations/\(vertexLocation)/publishers/google/models/\(model):generateContent"
        } else {
            // AI Studio: https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent
            components.host = "generativelanguage.googleapis.com"
            components.path = "/v1beta/models/\(model):generateContent"
            if case let .apiKey(key) = auth {
                components.queryItems = [URLQueryItem(name: "key", value: key)]
            }
        }

        guard let url = components.url else {
            throw GeminiRequestError.invalidURL
        }

        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        if case let .bearer(token) = auth {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }

        request.httpBody = try JSONSerialization.data(
            withJSONObject: [
                "contents": [
                    [
                        "role": "user",
                        "parts": [
                            ["text": prompt],
                            [
                                "inlineData": [
                                    "mimeType": "audio/wav",
                                    "data": audioData.base64EncodedString(),
                                ]
                            ],
                        ],
                    ]
                ]
            ]
        )
        return request
    }
}

public enum GeminiRequestError: Error {
    case invalidURL
}
