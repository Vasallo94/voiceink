// swift-tools-version: 6.0

import PackageDescription

let package = Package(
    name: "VoiceInk",
    platforms: [
        .macOS(.v13)
    ],
    products: [
        .library(name: "VoiceInkCore", targets: ["VoiceInkCore"]),
        .executable(name: "VoiceInk", targets: ["VoiceInk"]),
        .executable(name: "VoiceInkCoreSmokeTests", targets: ["VoiceInkCoreSmokeTests"]),
    ],
    targets: [
        .target(name: "VoiceInkCore"),
        .executableTarget(
            name: "VoiceInk",
            dependencies: ["VoiceInkCore"]
        ),
        .executableTarget(
            name: "VoiceInkCoreSmokeTests",
            dependencies: ["VoiceInkCore"]
        ),
    ]
)
