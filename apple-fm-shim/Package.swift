// swift-tools-version: 6.2
import PackageDescription

let package = Package(
    name: "apple-fm-shim",
    platforms: [.macOS(.v26)],
    targets: [.executableTarget(name: "apple-fm-shim")]
)
