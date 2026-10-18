# Assets

| Path | What it is |
|---|---|
| `viewer/viewer.html` | The 3D viewer (three.js). Every shape and texture is generated in code. `web/render3d.py` fills in the data and the import map. |
| `viewer/vendor/` | three.js r169 (`three.module.min.js`, `OrbitControls.js`, `BufferGeometryUtils.js`) with its MIT `LICENSE`, bundled so the viewer works without a network. Downloaded unchanged from `https://cdn.jsdelivr.net/npm/three@0.169.0/`. |
| `media/` | Optional decorative images and video (Higgsfield). None are included yet; see `PROMPTS.md`. |
| `PROMPTS.md` | Prompts, settings and status for generated media. |

Generated media is decorative and labeled as illustrative; it is never analytical evidence. A missing
media file never breaks a page.
