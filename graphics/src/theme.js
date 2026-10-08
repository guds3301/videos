// Cold Steel / Warm Core tokens. Keep in sync with fabrica-videos/style/STYLE_GUIDE.md.
export const palette = {
  black: '#07090C',
  graphite: '#171B20',
  steel: '#AAB4BC',
  white: '#EEF1F3',
  amber: '#F2A45A',
  red: '#E83B32',
  blue: '#4B86B4', // optional, only when the subject needs it
};

// Functional sans for labels and numbers. Install Inter for the intended look;
// the other families are fallbacks so a render never fails on a missing font.
export const sansFont = 'Inter, Manrope, "Segoe UI", "Helvetica Neue", Arial, "DejaVu Sans", sans-serif';

export const colorFor = (name, fallback = palette.white) => palette[name] ?? name ?? fallback;
