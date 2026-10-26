/** Read-only browser helper. Import/evaluate in the rendered page, not Node alone.
 * IDs map to {selector, textOnly?}; sourceImageSha256 binds a captured image.
 * CSS viewport coordinates; record devicePixelRatio for the actual screenshot.
 */
export function measureLayout(selectors, sourceImageSha256, pixelRatio = window.devicePixelRatio) {
  if (!/^[a-f0-9]{64}$/i.test(sourceImageSha256)) throw new Error('A captured image SHA-256 is required');
  if (!(Number.isFinite(pixelRatio) && pixelRatio > 0)) throw new Error('Invalid screenshot pixel ratio');
  const boxes = {};
  const missing = [];
  for (const [id, item] of Object.entries(selectors)) {
    const elements = document.querySelectorAll(item.selector);
    if (elements.length !== 1) { missing.push({id, count: elements.length}); continue; }
    const element = elements[0];
    const style = window.getComputedStyle(element);
    if (style.visibility === 'hidden' || style.display === 'none' || Number(style.opacity) === 0) {
      missing.push({id, reason: 'hidden'}); continue;
    }
    let rect;
    if (item.textOnly) {
      const range = document.createRange();
      range.selectNodeContents(element);
      rect = range.getBoundingClientRect();
    } else rect = element.getBoundingClientRect();
    if (!(rect.width > 0 && rect.height > 0)) { missing.push({id, reason: 'empty'}); continue; }
    boxes[id] = {x: rect.x, y: rect.y, width: rect.width, height: rect.height,
      font_size: Number.parseFloat(style.fontSize)};
  }
  return {version: 1, kind: 'observed', canvas: {width: window.innerWidth, height: window.innerHeight},
    pixel_ratio: pixelRatio, evidence: {method: 'dom', image_sha256: sourceImageSha256,
      uncertainty_px: 0, note: 'DOM geometry, not pixel/OCR recognition; keep viewport/scroll unchanged after capture'},
    boxes, missing};
}
