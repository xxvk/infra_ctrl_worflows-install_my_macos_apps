import Foundation
import IOKit.hid
import AppKit
import ApplicationServices

private let logURL = URL(fileURLWithPath: NSHomeDirectory())
    .appendingPathComponent("Library/Logs/install_my_macos_apps/keyboard-config-logi-k240.log")
private var pressedUsages = Set<UInt32>()
private var lastTriggerByUsage = [UInt32: Date]()

private func log(_ message: String) {
    let directory = logURL.deletingLastPathComponent()
    try? FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true)
    let line = "\(ISO8601DateFormatter().string(from: Date())) \(message)\n"
    if let data = line.data(using: .utf8) {
        if FileManager.default.fileExists(atPath: logURL.path),
           let handle = try? FileHandle(forWritingTo: logURL) {
            try? handle.seekToEnd()
            try? handle.write(contentsOf: data)
            try? handle.close()
        } else {
            try? data.write(to: logURL, options: .atomic)
        }
    }
}

private func runAction(for usage: UInt32) {
    let process = Process()
    switch usage {
    case 0x3a: // F1
        process.executableURL = URL(fileURLWithPath: "/usr/bin/open")
        process.arguments = ["/Applications/ChatGPT.app"]
    case 0x3b: // F2
        process.executableURL = URL(fileURLWithPath: "/usr/bin/open")
        process.arguments = ["/Applications/Claude.app"]
    case 0x3c: // F3
        process.executableURL = URL(fileURLWithPath: "/usr/bin/open")
        process.arguments = ["/Applications/Perplexity.app"]
    case 0x3e: // F5
        let standardYouTube = "/Applications/YouTube.app"
        let playCoverYouTube = URL(fileURLWithPath: NSHomeDirectory())
            .appendingPathComponent("Applications/PlayCover/YouTube.app").path
        if FileManager.default.fileExists(atPath: standardYouTube) {
            process.executableURL = URL(fileURLWithPath: "/usr/bin/open")
            process.arguments = ["-a", standardYouTube]
        } else if FileManager.default.fileExists(atPath: playCoverYouTube + "/YouTube") {
            if activateRunningApplication(bundleIdentifier: "com.google.ios.youtube") {
                log("F5 received; activated existing PlayCover YouTube")
                return
            }
            process.executableURL = URL(fileURLWithPath: playCoverYouTube + "/YouTube")
            process.arguments = []
        } else {
            process.executableURL = URL(fileURLWithPath: "/usr/bin/open")
            process.arguments = ["-a", "/System/Applications/Music.app"]
        }
    case 0x45: // F12
        process.executableURL = URL(fileURLWithPath: "/usr/bin/open")
        process.arguments = ["-a", "/System/Applications/Utilities/Screenshot.app"]
    default:
        return
    }
    do {
        try process.run()
        log("F\(usage - 0x39) received; started action for HID usage 0x\(String(usage, radix: 16))")
    } catch {
        log("Unable to start action for HID usage 0x\(String(usage, radix: 16)): \(error)")
    }
}

private func activateRunningApplication(bundleIdentifier: String) -> Bool {
    guard let application = NSRunningApplication
        .runningApplications(withBundleIdentifier: bundleIdentifier)
        .first else {
        return false
    }

    // Activation alone does not reliably restore a window minimized with the
    // yellow button. Unhide the app first, then clear AXMinimized on its
    // windows before activating it, matching the behavior of native apps.
    application.unhide()
    var restoredWindow = false
    let axApplication = AXUIElementCreateApplication(application.processIdentifier)
    var windowsValue: CFTypeRef?
    let copyResult = AXUIElementCopyAttributeValue(
        axApplication,
        kAXWindowsAttribute as CFString,
        &windowsValue
    )
    if copyResult == .success, let windows = windowsValue as? [AXUIElement] {
        for window in windows {
            if AXUIElementSetAttributeValue(
                window,
                kAXMinimizedAttribute as CFString,
                kCFBooleanFalse
            ) == .success {
                restoredWindow = true
            }
        }
    } else if copyResult != .success {
        log("Unable to inspect PlayCover YouTube windows for restoration: AXError \(copyResult.rawValue)")
    }

    let activated = application.activate(options: [.activateAllWindows])
    log("Restored existing PlayCover YouTube window: restored=\(restoredWindow) activated=\(activated)")
    return activated || restoredWindow
}

private func inputValueCallback(
    _ context: UnsafeMutableRawPointer?,
    _ result: IOReturn,
    _ sender: UnsafeMutableRawPointer?,
    _ value: IOHIDValue
) {
    let element = IOHIDValueGetElement(value)
    let usagePage = IOHIDElementGetUsagePage(element)
    let usage = IOHIDElementGetUsage(element)

    // USB HID Keyboard/Keypad page: F1-F3, F5, and F12.
    guard usagePage == 0x07, [0x3a, 0x3b, 0x3c, 0x3e, 0x45].contains(usage) else { return }

    let isDown = IOHIDValueGetIntegerValue(value) != 0
    if isDown {
        let now = Date()
        let lastTrigger = lastTriggerByUsage[usage] ?? .distantPast
        if !pressedUsages.contains(usage), now.timeIntervalSince(lastTrigger) > 0.5 {
            pressedUsages.insert(usage)
            lastTriggerByUsage[usage] = now
            runAction(for: usage)
        }
    } else {
        pressedUsages.remove(usage)
    }
}

let manager = IOHIDManagerCreate(kCFAllocatorDefault, IOOptionBits(kIOHIDOptionsTypeNone))
let matching: [String: Any] = [
    kIOHIDVendorIDKey as String: 0x046d,
    kIOHIDProductIDKey as String: 0xc534
]
IOHIDManagerSetDeviceMatching(manager, matching as CFDictionary)
IOHIDManagerRegisterInputValueCallback(manager, inputValueCallback, nil)
IOHIDManagerScheduleWithRunLoop(manager, CFRunLoopGetCurrent(), CFRunLoopMode.defaultMode.rawValue)

guard IOHIDManagerOpen(manager, IOOptionBits(kIOHIDOptionsTypeNone)) == kIOReturnSuccess else {
    log("Unable to open Logitech receiver; grant Input Monitoring permission if needed")
    exit(1)
}

log("Listening for Logitech receiver 046d:c534 F1, F2, F3, F5, F12")
CFRunLoopRun()
