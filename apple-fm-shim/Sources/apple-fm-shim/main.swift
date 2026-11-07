import Foundation
import FoundationModels

// Line-delimited JSON over stdio: one request per stdin line, one response per stdout line.
// Each request uses a fresh session, so no state leaks between chunks.

// Built dynamically: the @Generable macros need Xcode's macro plugin, which Command Line Tools lack.
func choice(_ name: String, _ values: [String]) -> DynamicGenerationSchema {
    DynamicGenerationSchema(name: name, anyOf: values)
}
func prop(_ name: String, _ schema: DynamicGenerationSchema, _ about: String? = nil) -> DynamicGenerationSchema.Property {
    .init(name: name, description: about, schema: schema)
}
let text = DynamicGenerationSchema(type: String.self)

let recordSchema = DynamicGenerationSchema(name: "Record", properties: [
    prop("quote", text, "Text copied character for character from the input. Never rephrase, shorten or fix it."),
    prop("type", choice("Type", ["claim", "requirement", "constraint", "decision", "question", "reference", "tangent"])),
    prop("modality", choice("Modality", ["stated", "hedged", "implied", "unspecified"]),
         "stated if asserted plainly, hedged if uncertain (maybe, might), implied if not said directly, unspecified if unclear."),
    prop("specificity", choice("Specificity", ["exact", "approximate", "vague", "unspecified"]),
         "exact if precise values are given, approximate if rough, vague if general, unspecified if no detail is given."),
    prop("entities", DynamicGenerationSchema(arrayOf: text, maximumElements: 6), "Names that appear inside the quote, copied exactly."),
])
let extractionSchema = try! GenerationSchema(
    root: DynamicGenerationSchema(name: "Extraction", properties: [prop("records", DynamicGenerationSchema(arrayOf: recordSchema, maximumElements: 15))]),
    dependencies: [])
let verdictSchema = try! GenerationSchema(
    root: DynamicGenerationSchema(name: "Verdict", properties: [prop("supported", DynamicGenerationSchema(type: Bool.self))]),
    dependencies: [])

let instructions = """
You extract records from text. Every record's quote must be copied exactly from the input. \
Never add detail the text does not state. If the text is vague, mark it vague. \
Do not merge or reorder statements. Cover every sentence that says something.
"""

// Greedy decoding loops on long structured output, so every run samples (seeded); output is capped: unbounded generation can run away until the 8192-token window is full, costing minutes per chunk.
func options(seed: Int, maxTokens: Int) -> GenerationOptions {
    GenerationOptions(sampling: .random(top: 40, seed: UInt64(seed + 1)), temperature: 0.3, maximumResponseTokens: maxTokens)
}

func extract(_ req: [String: Any]) async throws -> [String: Any] {
    let chunk = req["chunk"] as? String ?? ""
    let ledger = req["ledger"] as? [String] ?? []
    let seed = req["seed"] as? Int ?? 0
    let known = ledger.isEmpty ? "" : "Known names (for resolving pronouns only): \(ledger.joined(separator: ", "))\n\n"
    let session = LanguageModelSession(instructions: instructions)
    let out = try await session.respond(to: "\(known)Input:\n\(chunk)", schema: extractionSchema, options: options(seed: seed, maxTokens: 1200))
    let records = try out.content.value([GeneratedContent].self, forProperty: "records").map { r -> [String: Any] in
        var rec: [String: Any] = [:]
        for key in ["quote", "type", "modality", "specificity"] { rec[key] = try r.value(String.self, forProperty: key) }
        rec["entities"] = try r.value([String].self, forProperty: "entities")
        return rec
    }
    return ["records": records]
}

func verify(_ req: [String: Any]) async throws -> [String: Any] {
    let session = LanguageModelSession(instructions: "You check whether a quote supports labels attached to it. Judge only from the quote.")
    let prompt = """
    Quote: \(req["quote"] as? String ?? "")
    Type: \(req["type"] as? String ?? "")
    Modality: \(req["modality"] as? String ?? "")
    Specificity: \(req["specificity"] as? String ?? "")
    Is every label supported by the quote, without adding detail the quote does not contain?
    """
    let out = try await session.respond(to: prompt, schema: verdictSchema, options: options(seed: 0, maxTokens: 100))
    return ["supported": try out.content.value(Bool.self, forProperty: "supported")]
}

func handle(_ req: [String: Any]) async throws -> [String: Any] {
    let model = SystemLanguageModel.default
    switch req["op"] as? String {
    case "info":
        if case .unavailable(let why) = model.availability { return ["available": false, "reason": "\(why)"] }
        return ["available": true, "contextSize": model.contextSize]
    case "tokens":
        guard #available(macOS 26.4, *) else { return ["error": "tokenCount needs macOS 26.4"] }
        return ["tokens": try await model.tokenCount(for: req["text"] as? String ?? "")]
    case "extract": return try await extract(req)
    case "verify": return try await verify(req)
    default: return ["error": "unknown op"]
    }
}

func emit(_ obj: [String: Any]) {
    let data = try! JSONSerialization.data(withJSONObject: obj)
    print(String(decoding: data, as: UTF8.self))
    fflush(stdout)
}

while let line = readLine() {
    guard let req = try? JSONSerialization.jsonObject(with: Data(line.utf8)) as? [String: Any] else {
        emit(["error": "invalid json"]); continue
    }
    do { emit(try await handle(req)) } catch { emit(["error": "\(error)"]) }
}
