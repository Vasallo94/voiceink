import Foundation

public enum GeminiAuth: Sendable {
    case apiKey(String)
    case bearer(String)
}

public protocol GeminiAuthProvider: Sendable {
    func auth() async throws -> GeminiAuth
}

public struct APIKeyAuthProvider: GeminiAuthProvider {
    private let resolver: APIKeyResolver

    public init(resolver: APIKeyResolver) {
        self.resolver = resolver
    }

    public func auth() async throws -> GeminiAuth {
        .apiKey(try resolver.resolveGeminiAPIKey())
    }
}
