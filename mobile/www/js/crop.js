// Crop disease library (always works) + optional photo check with onnxruntime-web.
import { REMEDIES } from "./data.js";
import { interpret } from "./labels.js";

export const crops = () => REMEDIES.crops;
export const diseasesFor = (cropId) => REMEDIES.diseases.filter((d) => d.crop === cropId);
export const disease = (id) => REMEDIES.diseases.find((d) => d.id === id) || null;

export const CONFIDENCE_THRESHOLD = 0.6;

/** What the app should do with the model's top guess (same rule as the Linux app). */
export function decide(top) {
  const [raw, p] = top;
  if (p < CONFIDENCE_THRESHOLD) return { kind: "unsure", p, raw };
  return { ...interpret(raw), p, raw };
}

export function softmaxTop(logits, labels, top = 3) {
  let max = -Infinity;
  for (const v of logits) if (v > max) max = v;
  const e = Array.from(logits, (v) => Math.exp(v - max));
  const sum = e.reduce((a, b) => a + b, 0);
  return e.map((v, i) => [labels[i], v / sum]).sort((a, b) => b[1] - a[1]).slice(0, top);
}

/** Loads models/crop_model.onnx (+ crop_labels.json). Returns null when the files are not there. */
export async function loadPredictor(base = "models/") {
  try {
    const lr = await fetch(base + "crop_labels.json");
    if (!lr.ok) return null;
    const cfg = await lr.json();
    const ort = await import("../vendor/ort.min.mjs");
    ort.env.wasm.wasmPaths = new URL("../vendor/", import.meta.url).href;
    const session = await ort.InferenceSession.create(base + "crop_model.onnx", { executionProviders: ["wasm"] });
    return new Predictor(ort, session, cfg);
  } catch (e) {
    return null;
  }
}

class Predictor {
  constructor(ort, session, cfg) {
    this.ort = ort; this.session = session; this.labels = cfg.labels;
    this.mean = cfg.mean || [0.485, 0.456, 0.406];
    this.std = cfg.std || [0.229, 0.224, 0.225];
    this.size = cfg.size || 224;
    this.resize = cfg.resize || null;
    this.input = session.inputNames[0];
  }
  async prepare(file) {
    const bmp = await createImageBitmap(file);
    const S = this.size;
    const cv = document.createElement("canvas");
    cv.width = S; cv.height = S;
    const ctx = cv.getContext("2d", { willReadFrequently: true });
    ctx.imageSmoothingQuality = "high";
    if (this.resize && this.resize !== S) {
      const scale = this.resize / Math.min(bmp.width, bmp.height);
      const w = Math.max(S, Math.round(bmp.width * scale)), h = Math.max(S, Math.round(bmp.height * scale));
      ctx.drawImage(bmp, -Math.floor((w - S) / 2), -Math.floor((h - S) / 2), w, h);
    } else {
      ctx.drawImage(bmp, 0, 0, S, S);
    }
    const px = ctx.getImageData(0, 0, S, S).data;
    const out = new Float32Array(3 * S * S);
    for (let i = 0; i < S * S; i++) {
      for (let c = 0; c < 3; c++) out[c * S * S + i] = (px[i * 4 + c] / 255 - this.mean[c]) / this.std[c];
    }
    return new this.ort.Tensor("float32", out, [1, 3, S, S]);
  }
  async predict(file, top = 3) {
    const res = await this.session.run({ [this.input]: await this.prepare(file) });
    return softmaxTop(res[this.session.outputNames[0]].data, this.labels, top);
  }
}
