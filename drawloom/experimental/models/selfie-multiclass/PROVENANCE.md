# Local hair region mask

Model: MediaPipe Selfie Multiclass 256×256 float32, version 1.

Source: https://storage.googleapis.com/mediapipe-models/image_segmenter/selfie_multiclass_256x256/float32/1/selfie_multiclass_256x256.tflite

Unmodified file: `model.tflite`, 16,371,837 bytes.
SHA256: `c6748b1253a99067ef71f7e26ca71096cd449baefa8f101900ea23016507e0e0`.

The original model card is retained as `model-card.pdf`. It identifies Google/Adel Ahmadyan, model date May 10, 2023, and Apache License 2.0. The MediaPipe v0.10.35 Apache license is included as `LICENSE.txt`. Official class indices are background 0, hair 1, body skin 2, face skin 3, clothes 4 and accessories 5. The model card warns that masks are approximate and can degrade with occluders, noise or lighting; no pixel-perfect claim is made.

`hair-tone.ts` verifies the bundled model hash and uses the installed Tasks Vision package with version-matched 0.10.35 WASM and CPU inference. It reads the returned category mask's own width and height, builds a class-1 alpha mask, and expands that mask to the original selected-person crop size with nearest-neighbor sampling. Inference is local; the photograph is not uploaded.

The native tone pass is a separate user-controlled operation. It repeats one fixed pattern only inside dark source hair (luminance <0.48), excludes a corridor around existing ink, and admits a cell only when its complete footprint stays inside the mask. It replaces open native paper, never an existing ink glyph. Left/right gap representability checks preserve existing ink-word positions exactly; unrepresentable tone cells are skipped. Mask error and a conservative footprint test can leave some hair unfilled. Inspect the actual result before retaining it.
