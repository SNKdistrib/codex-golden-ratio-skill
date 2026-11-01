# Strict 2D / 3D delivery (v0.2.0)

This workflow adds executable checks, not a claim of universal beauty or control of
model reasoning. Design decisions must appear in a concise external geometry contract.
Preserve existing identity, content, requested format and explicit alignments.

## Required order

1. Write a plan and its geometry contract. Include every geometry layer/object.
2. Run `golden_delivery.py begin --plan plan.json --job job.json` before rendering.
3. Render new candidate/evidence files. Never substitute manually invented boxes.
4. Run `golden_delivery.py check --job job.json` and inspect the real output.
5. Only after PASS: `golden_delivery.py export --job job.json --out final.png`.
6. The receipt is `final.png.golden.json`. Revalidate it using
   `golden_delivery.py receipt --path final.png.golden.json`.

`begin` hashes the plan, geometry contract and optional protected source inputs.
Changing these bindings invalidates the job. This establishes an enforced order for
this pipeline, not cryptographic trust against someone rewriting all files.
Candidate and layer paths must not exist when preparing. Reusing an old image after
begin does not prove it was originally designed under the new contract.

Python 3 + Pillow are required for strict verification. Install dependencies only
within the user's approved environment. Missing Pillow returns UNVERIFIED, never PASS.
Legacy `verify_layout.py` and `export_verified.py` remain scoped diagnostic tools.

## Plan schema

Paths are relative to the plan, or absolute. Example for an isolated three-part logo:

```json
{
  "version": 2,
  "mode": "layout",
  "scope": "Original logo: shared left edge, shared bottom, width cap and height ratio",
  "canvas": [600, 200],
  "background": "transparent",
  "image": "candidate.png",
  "contract": "contract.json",
  "protected_inputs": ["official-source.png", "render.js"],
  "layers": [
    {"id":"mark", "path":"mark.png", "role":"geometry"},
    {"id":"wordmark", "path":"wordmark.png", "role":"geometry"},
    {"id":"tagline", "path":"tagline.png", "role":"geometry"}
  ]
}
```

`mode` is `layout` or `scene`. `background` is explicitly `transparent` or `opaque`.
Layers are full-canvas RGBA PNGs in back-to-front composition order. A decoration
layer needs `role:"decoration"` and a specific `reason`; it is still recomposed and
hashed. Do not hide important geometry by classifying it as decoration.

Layout contracts use the existing schema in [verification.md](verification.md).
Strict full-creation delivery requires a direct phi ratio (`ratio`, exponent 1, or
a declared lockup height exponent 1). A centering-only repair uses the legacy scoped
profile and must not be advertised as a globally golden redesign.

The verifier derives visible-ink bounds at alpha >=128 from actual layers. It checks
their exact final alpha and opaque RGB recomposition. Only 1-byte RGB rounding on
translucent antialiasing edges is accepted. A transparent canvas requires four clear
corners. These checks are not OCR, optical centering, identity recognition or proof
that the renderer actually used every protected input. Brand preservation still
requires inspection/source-native reuse.

## Three-dimensional contracts

Use evaluated, transform-baked **world vertices**, not axis-aligned bounding-box
dimensions that change when a model rotates. Export from the actual scene used for
rendering. Never recover presumed depth from a single raster image.

A scene plan additionally declares `scene:"scene.json"` and seals `camera` with:

```json
{"viewport":[800,600],"world_to_clip":[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1]}
```

The example matrix is identity for schema illustration, not a recommended camera.
The matrix is row-major, OpenGL clip convention: homogeneous division, NDC in [-1,1],
top-left raster origin. Use the actual renderer's view-projection matrix. Camera
changes invalidate the sealed plan. Clipped vertices are rejected; this release
does not implement near-plane clipping, curved/deformed procedural surfaces or lens distortion.

Scene data:

```json
{
 "version":1,"coordinate_space":"world",
 "camera":{"viewport":[800,600],"world_to_clip":[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1]},
 "objects":{"shape":{"vertices":[[0,0,0],[0.8,0,0],[0,0.494427191,0]],"faces":[[0,1,2]]}}
}
```

Contract rules measure distances between named vertex pairs. `space` is required:
`world` for physical geometry, `projected` for its actual camera projection.

```json
{
 "version":1,"inventory":["shape"],
 "rules":[{
  "id":"main-proportion","type":"ratio","space":"world","structural":true,
  "a":{"object":"shape","vertices":[0,1]},
  "b":{"object":"shape","vertices":[0,2]},
  "exponent":1,"tolerance_pct":1
 }]
}
```

At least one structural direct phi ratio is required. Other supported powers are
-2,-1,-0.5,0.5,1,2,3,4,5,6. Zero cannot manufacture conformity. `align` rules use
`points:[{"object":"shape","vertex":0},...]`, `axis` (0/1/2 in world, 0/1 projected)
and an explicit `tolerance` in the named space's units. Every exported object must
have a checked relation or an explicit `preserved:{"id":"reason"}` entry.

Each object's isolated layer must match the rasterized union of its projected faces
within a one-pixel boundary band. This independently ties the geometric silhouette
to actual output pixels. Composite layers must also reproduce the delivered PNG.
It does not validate texture, lighting, inter-object depth sorting or physical realism.
Perspective need not preserve phi on screen. Never claim a world ratio is also a
projected ratio unless a separate rule actually checked it.

## Codex hook scope and activation

Optional local hooks call `scripts/codex_guard.py` for UserPromptSubmit, PreToolUse
and Stop. They use session-specific state under `~/.codex/golden-guard` (override
`GOLDEN_STATE_DIR` for tests). CLI `begin` registers a job using `CODEX_THREAD_ID`.
The command's output includes `session_id`; if absent, Stop enforcement is not armed.

The prompt hook adds a routing reminder. The tool hook denies recognized `imagegen`
calls without a prepared job. The Stop hook revalidates registered export receipts
and requests correction if missing or stale. After one continuation it stops with
an explicit failure rather than looping. It does not prevent unrelated nonvisual work.

Install hooks only on explicit request. Use normal `/hooks` review/trust in Codex;
never change trust databases or use bypass flags. New/changed untrusted hooks are
skipped by Codex. Installation, simulated handler tests and actual host activation
are three separate statuses. Do not call the hook active without a host observation.

Coverage is not universal: opaque shell commands, unrecognized tools and direct
unregistered paths can escape this guard. Stop cannot retract media a tool already
displayed. Keep generated previews labeled as drafts. These scripts are not a
security boundary against the agent/user who can edit them. See the official
[Codex hook contract](https://learn.chatgpt.com/docs/hooks).

## Verification and reports

Run all tests: `python -m unittest discover -s tests -v`. Tests include real raster
mutations, missing evidence, stale receipts, a mesh with camera projection and
simulated lifecycle decisions. They do not establish activation in a live Codex host
or behavioral reliability across every prompt. Record actual integration exercises
separately. A local PASS never becomes `global_composition_conformity: ESTABLISHED`.
