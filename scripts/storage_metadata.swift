import Foundation

struct HelperFailure: Error, CustomStringConvertible {
    let description: String
}

func jsonValue(_ value: Any?) -> Any {
    value ?? NSNull()
}

func inspect(_ url: URL) throws -> [String: Any] {
    let keys: Set<URLResourceKey> = [
        .isUbiquitousItemKey,
        .ubiquitousItemDownloadingStatusKey,
        .ubiquitousItemIsUploadedKey,
        .ubiquitousItemIsUploadingKey,
        .ubiquitousItemIsDownloadingKey,
        .ubiquitousItemHasUnresolvedConflictsKey,
        .fileAllocatedSizeKey,
        .totalFileAllocatedSizeKey,
        .fileResourceIdentifierKey,
        .volumeUUIDStringKey,
        .volumeAvailableCapacityKey,
    ]
    let values = try url.resourceValues(forKeys: keys)
    let status = values.ubiquitousItemDownloadingStatus?.rawValue
    let ubiquitous = values.isUbiquitousItem ?? false
    return [
        "provider": ubiquitous ? "icloud" : "none",
        "is_ubiquitous": ubiquitous,
        "is_uploaded": jsonValue(values.ubiquitousItemIsUploaded),
        "is_uploading": jsonValue(values.ubiquitousItemIsUploading),
        "is_downloading": jsonValue(values.ubiquitousItemIsDownloading),
        "has_unresolved_conflicts": jsonValue(values.ubiquitousItemHasUnresolvedConflicts),
        "downloading_status": jsonValue(status),
        "is_dataless": status == URLUbiquitousItemDownloadingStatus.notDownloaded.rawValue,
        "file_allocated_bytes": jsonValue(values.fileAllocatedSize),
        "total_allocated_bytes": jsonValue(values.totalFileAllocatedSize),
        "resource_identifier": jsonValue(values.fileResourceIdentifier.map { String(describing: $0) }),
        "volume_uuid": jsonValue(values.volumeUUIDString),
        "volume_available_bytes": jsonValue(values.volumeAvailableCapacity),
    ]
}

func emit(_ value: [String: Any]) throws {
    let data = try JSONSerialization.data(withJSONObject: value, options: [.prettyPrinted, .sortedKeys])
    FileHandle.standardOutput.write(data)
    FileHandle.standardOutput.write(Data("\n".utf8))
}

do {
    guard CommandLine.arguments.count == 3 else {
        throw HelperFailure(description: "usage: storage-metadata inspect|evict|download|trash PATH")
    }
    let command = CommandLine.arguments[1]
    let url = URL(fileURLWithPath: CommandLine.arguments[2])
    switch command {
    case "inspect":
        try emit(inspect(url))
    case "evict":
        let before = try inspect(url)
        guard before["is_ubiquitous"] as? Bool == true else {
            throw HelperFailure(description: "path is not an iCloud ubiquitous item")
        }
        try FileManager.default.evictUbiquitousItem(at: url)
        try emit(["status": "eviction_requested", "path": url.path])
    case "download":
        try FileManager.default.startDownloadingUbiquitousItem(at: url)
        try emit(["status": "download_requested", "path": url.path])
    case "trash":
        var resulting: NSURL?
        try FileManager.default.trashItem(at: url, resultingItemURL: &resulting)
        guard let destination = resulting as URL? else {
            throw HelperFailure(description: "Trash operation returned no resulting path")
        }
        try emit(["status": "staged", "resulting_path": destination.path])
    default:
        throw HelperFailure(description: "unknown command: \(command)")
    }
} catch {
    FileHandle.standardError.write(Data("\(error)\n".utf8))
    exit(2)
}
