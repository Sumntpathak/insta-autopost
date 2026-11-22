import {useEffect, useState} from 'react';
import {continueRender, delayRender, staticFile} from 'remotion';
const FACES: [string, string, string][] = [
  ['Playfair Display', '700', 'playfair-display-latin-700-normal.woff2'],
  ['Playfair Display', '800', 'playfair-display-latin-800-normal.woff2'],
  ['Poppins', '500', 'poppins-latin-500-normal.woff2'],
  ['Poppins', '600', 'poppins-latin-600-normal.woff2'],
  ['Poppins', '700', 'poppins-latin-700-normal.woff2'],
];
export const useFonts = () => {
  const [h] = useState(() => delayRender('fonts'));
  useEffect(() => {
    Promise.all(FACES.map(async ([fam, w, f]) => {
      const ff = new FontFace(fam, `url(${staticFile('fonts/' + f)})`, {weight: w});
      await ff.load();
      document.fonts.add(ff);
    })).then(() => continueRender(h));
  }, [h]);
};
