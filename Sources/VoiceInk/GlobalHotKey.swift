import Carbon.HIToolbox
import Foundation
import VoiceInkCore

@MainActor
final class GlobalHotKey {
    private var hotKeyRef: EventHotKeyRef?
    private var eventHandlerRef: EventHandlerRef?
    private let descriptor: HotKeyDescriptor
    private let onPressed: @MainActor () -> Void

    init(
        descriptor: HotKeyDescriptor = .default,
        onPressed: @escaping @MainActor () -> Void
    ) {
        self.descriptor = descriptor
        self.onPressed = onPressed
    }

    var displayName: String {
        descriptor.displayName
    }

    func register() throws {
        unregister()

        let hotKeyID = EventHotKeyID(
            signature: OSType(UInt32(ascii: "V2CH")),
            id: 1
        )

        var eventSpec = EventTypeSpec(
            eventClass: OSType(kEventClassKeyboard),
            eventKind: UInt32(kEventHotKeyPressed)
        )

        let handlerStatus = InstallEventHandler(
            GetApplicationEventTarget(),
            { _, _, userData in
                guard let userData else {
                    return noErr
                }

                let hotKey = Unmanaged<GlobalHotKey>
                    .fromOpaque(userData)
                    .takeUnretainedValue()

                Task { @MainActor in
                    hotKey.onPressed()
                }

                return noErr
            },
            1,
            &eventSpec,
            Unmanaged.passUnretained(self).toOpaque(),
            &eventHandlerRef
        )

        guard handlerStatus == noErr else {
            throw GlobalHotKeyError.installHandlerFailed(handlerStatus)
        }

        let registerStatus = RegisterEventHotKey(
            descriptor.keyCode,
            carbonModifierFlags(for: descriptor.modifiers),
            hotKeyID,
            GetApplicationEventTarget(),
            0,
            &hotKeyRef
        )

        guard registerStatus == noErr else {
            unregister()
            throw GlobalHotKeyError.registerFailed(registerStatus)
        }
    }

    func unregister() {
        if let hotKeyRef {
            UnregisterEventHotKey(hotKeyRef)
            self.hotKeyRef = nil
        }

        if let eventHandlerRef {
            RemoveEventHandler(eventHandlerRef)
            self.eventHandlerRef = nil
        }
    }

    private func carbonModifierFlags(for modifiers: [HotKeyModifier]) -> UInt32 {
        modifiers.reduce(UInt32(0)) { result, modifier in
            switch modifier {
            case .command:
                result | UInt32(cmdKey)
            case .control:
                result | UInt32(controlKey)
            case .option:
                result | UInt32(optionKey)
            case .shift:
                result | UInt32(shiftKey)
            }
        }
    }
}

enum GlobalHotKeyError: Error, LocalizedError {
    case installHandlerFailed(OSStatus)
    case registerFailed(OSStatus)

    var errorDescription: String? {
        switch self {
        case let .installHandlerFailed(status):
            "Could not install hotkey handler: \(status)"
        case let .registerFailed(status):
            "Could not register global hotkey: \(status)"
        }
    }
}

private extension UInt32 {
    init(ascii string: String) {
        self = string.utf8.reduce(UInt32(0)) { value, character in
            (value << 8) + UInt32(character)
        }
    }
}
