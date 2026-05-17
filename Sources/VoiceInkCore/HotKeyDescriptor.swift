import Foundation

public struct HotKeyDescriptor: Equatable, Sendable {
    public let keyCode: UInt32
    public let modifiers: [HotKeyModifier]
    public let displayName: String

    public static let `default` = HotKeyDescriptor(
        keyCode: 1,
        modifiers: [.control, .shift],
        displayName: "Ctrl+Shift+S"
    )

    public init(keyCode: UInt32, modifiers: [HotKeyModifier], displayName: String) {
        self.keyCode = keyCode
        self.modifiers = modifiers
        self.displayName = displayName
    }
}

public enum HotKeyModifier: String, Equatable, Sendable {
    case command
    case control
    case option
    case shift
}
