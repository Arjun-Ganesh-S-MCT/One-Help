// Turns the model's raw class names (PlantVillage style, e.g. "Tomato___Late_blight") into
// something the app understands. Same rules as oru/labels.py.
import { LABEL_RULES } from "./data.js";

const norm = (raw) => raw.toLowerCase().replace(/[^a-z0-9]+/g, " ").trim();

export function pretty(raw) {
  const parts = raw.split(/_{2,}/).filter(Boolean)
    .map((p) => p.replace(/_+/g, " ").replace(/[()]/g, "").trim());
  return parts.map((p) => p.charAt(0).toUpperCase() + p.slice(1)).join(" - ");
}

/** -> { kind: "disease" | "healthy" | "other", crop, diseaseId, pretty } */
export function interpret(raw) {
  const words = new Set(norm(raw).split(" ").filter(Boolean));
  const crop = words.has("tomato") ? "tomato" : words.has("potato") ? "potato" : "";
  const name = pretty(raw);
  if (words.has("healthy")) return { kind: "healthy", crop, diseaseId: "", pretty: name };
  for (const r of LABEL_RULES) {
    if (r.crop === crop && r.must.every((m) => [...words].some((w) => w.startsWith(m)))) {
      return { kind: "disease", crop, diseaseId: r.id, pretty: name };
    }
  }
  return { kind: "other", crop, diseaseId: "", pretty: name };
}
