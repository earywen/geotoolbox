# IMPL: UI/UX Visual Polish

## Goal Description
Enhance the "professional feel" of the application through micro-interactions, consistent feedback mechanisms (Toasts), and refined visual states.

## Proposed Changes

### [Frontend]
#### [MODIFY] [assets/js/app.js](file:///f:/Vibecoding/geotoolbox/assets/js/app.js)
- Ensure `showToast` is robust and globally exposed.
- Scan for `alert()` calls and replace them with `showToast`.

#### [MODIFY] [assets/css/style.css](file:///f:/Vibecoding/geotoolbox/assets/css/style.css)
- Add `.skeleton` class for loading states.
- Enhance `.carto-card` and `.dock-item` with subtle `transform: scale()` and `box-shadow` transitions on hover.
- Add `@keyframes pulse-glow` for the generic Call-to-Action buttons.
- **NEW**: Redesign "Export" buttons to match Magic UI aesthetics (Shimmer/Glow effects). Make them consistency sized (full width or 50/50).

#### [MODIFY] [assets/templates/cartographie.html](file:///f:/Vibecoding/geotoolbox/assets/templates/cartographie.html)
- Standardize button classes in the export section.
- **NEW**: Replace emojis with Lucide Icons (`<i data-lucide="..."></i>`).
- Add Lucide CDN script.

#### [MODIFY] [assets/js/cartographie.js](file:///f:/Vibecoding/geotoolbox/assets/js/cartographie.js)
- Add skeleton loader to `loadLayers()` while fetching config.
- Trigger pulse animation on "Export" button when bbox is drawn.
- **NEW**: Call `lucide.createIcons()` in `init()` and after dynamic content updates.

## Verification Plan
- **Visual**: Hover over dock items, cards, and buttons to see smooth transitions.
- **Functional**: Trigger an error (e.g., undraw polygon and click export) to verify `showToast` appears instead of `alert`.
