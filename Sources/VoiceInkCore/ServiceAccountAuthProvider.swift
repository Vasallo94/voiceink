import Foundation
import Security

// MARK: - Credentials

public struct ServiceAccountCredentials: Sendable {
    public let projectId: String
    public let clientEmail: String
    public let privateKeyPEM: String
    public let tokenURI: String

    public init(from fileURL: URL) throws {
        let data = try Data(contentsOf: fileURL)
        let json = try JSONDecoder().decode(ServiceAccountJSON.self, from: data)
        guard json.type == "service_account" else {
            throw ServiceAccountError.invalidType(json.type)
        }
        projectId = json.projectId
        clientEmail = json.clientEmail
        privateKeyPEM = json.privateKey
        tokenURI = json.tokenURI
    }
}

private struct ServiceAccountJSON: Decodable {
    let type: String
    let projectId: String
    let clientEmail: String
    let privateKey: String
    let tokenURI: String

    enum CodingKeys: String, CodingKey {
        case type
        case projectId = "project_id"
        case clientEmail = "client_email"
        case privateKey = "private_key"
        case tokenURI = "token_uri"
    }
}

// MARK: - Token cache

private struct CachedToken: Sendable {
    let accessToken: String
    let expiresAt: Date

    var isValid: Bool { Date() < expiresAt }
}

private struct TokenResponse: Decodable {
    let accessToken: String
    let expiresIn: Int

    enum CodingKeys: String, CodingKey {
        case accessToken = "access_token"
        case expiresIn = "expires_in"
    }
}

// MARK: - Provider

/// Authenticates with Google APIs using a service account JSON file.
/// Fetches OAuth 2.0 Bearer tokens (1-hour TTL) and caches them to avoid
/// unnecessary token exchanges between recordings.
public actor ServiceAccountAuthProvider: GeminiAuthProvider {
    private let credentials: ServiceAccountCredentials
    private let urlSession: URLSession
    private var cachedToken: CachedToken?

    public init(credentials: ServiceAccountCredentials, urlSession: URLSession = .shared) {
        self.credentials = credentials
        self.urlSession = urlSession
    }

    public func auth() async throws -> GeminiAuth {
        if let cached = cachedToken, cached.isValid {
            return .bearer(cached.accessToken)
        }
        let token = try await fetchAccessToken()
        cachedToken = token
        return .bearer(token.accessToken)
    }

    // MARK: - Token exchange

    private func fetchAccessToken() async throws -> CachedToken {
        let now = Date()
        let jwt = try makeJWT(issuedAt: now)

        var request = URLRequest(url: URL(string: credentials.tokenURI)!)
        request.httpMethod = "POST"
        request.setValue("application/x-www-form-urlencoded", forHTTPHeaderField: "Content-Type")
        request.httpBody =
            "grant_type=urn%3Aietf%3Aparams%3Aoauth%3Agrant-type%3Ajwt-bearer&assertion=\(jwt)"
            .data(using: .utf8)

        let (data, response) = try await urlSession.data(for: request)
        if let httpResponse = response as? HTTPURLResponse,
            !(200..<300).contains(httpResponse.statusCode)
        {
            let detail = String(data: data, encoding: .utf8) ?? "HTTP \(httpResponse.statusCode)"
            throw ServiceAccountError.tokenRequestFailed(detail)
        }

        let tokenResponse = try JSONDecoder().decode(TokenResponse.self, from: data)
        // Subtract 60s so we refresh before actual expiry
        return CachedToken(
            accessToken: tokenResponse.accessToken,
            expiresAt: now.addingTimeInterval(Double(tokenResponse.expiresIn) - 60)
        )
    }

    // MARK: - JWT

    private func makeJWT(issuedAt: Date) throws -> String {
        let header = #"{"alg":"RS256","typ":"JWT"}"#
        let iat = Int(issuedAt.timeIntervalSince1970)
        let exp = iat + 3600
        let claims = """
            {"iss":"\(credentials.clientEmail)",\
            "scope":"https://www.googleapis.com/auth/cloud-platform",\
            "aud":"\(credentials.tokenURI)",\
            "iat":\(iat),"exp":\(exp)}
            """

        let headerEncoded = base64URLEncode(Data(header.utf8))
        let claimsEncoded = base64URLEncode(Data(claims.utf8))
        let signingInput = "\(headerEncoded).\(claimsEncoded)"

        let signature = try rsaSign(
            message: Data(signingInput.utf8), pemKey: credentials.privateKeyPEM)
        return "\(signingInput).\(base64URLEncode(signature))"
    }

    // MARK: - RSA-SHA256 signing

    /// Signs with PKCS#1 v1.5 / SHA-256 using the PKCS#8 PEM key from the SA JSON.
    /// SecItemImport handles PKCS#8 unwrapping natively on macOS 13+,
    /// avoiding the need for a manual DER parser.
    private func rsaSign(message: Data, pemKey: String) throws -> Data {
        let secKey = try importPrivateKey(pem: pemKey)

        var error: Unmanaged<CFError>?
        guard
            let signature = SecKeyCreateSignature(
                secKey,
                .rsaSignatureMessagePKCS1v15SHA256,
                message as CFData,
                &error
            )
        else {
            throw ServiceAccountError.signingFailed(
                error?.takeRetainedValue().localizedDescription ?? "unknown error")
        }

        return signature as Data
    }

    /// Imports a PKCS#8 PEM private key (Google SA format) as a SecKey.
    /// SecItemImport requires a keychain on modern macOS, so we parse the PKCS#8
    /// DER wrapper manually to extract the inner PKCS#1 key and pass it directly
    /// to SecKeyCreateWithData, which accepts PKCS#1 without a keychain.
    private func importPrivateKey(pem: String) throws -> SecKey {
        // Strip PEM armor and decode base64 to get PKCS#8 DER bytes
        let stripped =
            pem
            .components(separatedBy: "\n")
            .filter { !$0.hasPrefix("-----") && !$0.isEmpty }
            .joined()

        guard let pkcs8DER = Data(base64Encoded: stripped) else {
            throw ServiceAccountError.keyImportFailed("Failed to base64-decode PEM key")
        }

        let pkcs1DER = try extractPKCS1FromPKCS8(pkcs8DER)

        let attributes: [String: Any] = [
            kSecAttrKeyType as String: kSecAttrKeyTypeRSA,
            kSecAttrKeyClass as String: kSecAttrKeyClassPrivate,
        ]
        var cfError: Unmanaged<CFError>?
        guard
            let secKey = SecKeyCreateWithData(
                pkcs1DER as CFData, attributes as CFDictionary, &cfError)
        else {
            throw ServiceAccountError.keyImportFailed(
                cfError?.takeRetainedValue().localizedDescription ?? "SecKeyCreateWithData failed")
        }
        return secKey
    }

    /// Parses a PKCS#8 DER blob and returns the inner PKCS#1 RSA private key bytes.
    /// PKCS#8 structure: SEQUENCE { INTEGER(0), SEQUENCE{OID,NULL}, OCTET STRING{PKCS#1} }
    private func extractPKCS1FromPKCS8(_ der: Data) throws -> Data {
        var i = der.startIndex

        // Outer SEQUENCE
        try expectTag(0x30, in: der, at: &i)
        try skipLength(in: der, at: &i)

        // INTEGER 0 (version)
        try expectTag(0x02, in: der, at: &i)
        let vLen = try readLength(in: der, at: &i)
        i = der.index(i, offsetBy: vLen)

        // AlgorithmIdentifier SEQUENCE
        try expectTag(0x30, in: der, at: &i)
        let aLen = try readLength(in: der, at: &i)
        i = der.index(i, offsetBy: aLen)

        // OCTET STRING containing PKCS#1 key
        try expectTag(0x04, in: der, at: &i)
        let kLen = try readLength(in: der, at: &i)

        return der[i..<der.index(i, offsetBy: kLen)]
    }

    private func expectTag(_ tag: UInt8, in data: Data, at index: inout Data.Index) throws {
        guard index < data.endIndex, data[index] == tag else {
            throw ServiceAccountError.keyImportFailed(
                "Unexpected DER tag at offset \(data.distance(from: data.startIndex, to: index))")
        }
        index = data.index(after: index)
    }

    private func skipLength(in data: Data, at index: inout Data.Index) throws {
        _ = try readLength(in: data, at: &index)
    }

    private func readLength(in data: Data, at index: inout Data.Index) throws -> Int {
        guard index < data.endIndex else {
            throw ServiceAccountError.keyImportFailed("Truncated DER data while reading length")
        }
        let first = data[index]
        index = data.index(after: index)
        if first & 0x80 == 0 { return Int(first) }
        let numBytes = Int(first & 0x7f)
        var length = 0
        for _ in 0..<numBytes {
            guard index < data.endIndex else {
                throw ServiceAccountError.keyImportFailed("Truncated DER length encoding")
            }
            length = (length << 8) | Int(data[index])
            index = data.index(after: index)
        }
        return length
    }

    // MARK: - Helpers

    private func base64URLEncode(_ data: Data) -> String {
        data.base64EncodedString()
            .replacingOccurrences(of: "+", with: "-")
            .replacingOccurrences(of: "/", with: "_")
            .replacingOccurrences(of: "=", with: "")
    }
}

// MARK: - Errors

public enum ServiceAccountError: Error, LocalizedError {
    case invalidType(String)
    case keyImportFailed(String)
    case signingFailed(String)
    case tokenRequestFailed(String)

    public var errorDescription: String? {
        switch self {
        case let .invalidType(type):
            "Service account JSON has unexpected type '\(type)' (expected 'service_account')"
        case let .keyImportFailed(detail):
            "Failed to import RSA private key: \(detail)"
        case let .signingFailed(detail):
            "Failed to sign JWT: \(detail)"
        case let .tokenRequestFailed(detail):
            "Token request failed: \(detail)"
        }
    }
}
