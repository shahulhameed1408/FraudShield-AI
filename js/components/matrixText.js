/**
 * FraudShield AI - Matrix Scramble Text Effect
 * Creates a futuristic cyberpunk decipher/decoding animation on button text.
 */

const CYBER_CHARS = '0123456789ABCDEF$#@%&*<>~_';

/**
 * Animates text scrambling on a target DOM element
 * @param {HTMLElement} element Target element whose textContent will scramble
 * @param {string} finalText The target final text string
 * @param {number} duration Duration in milliseconds (default: 800ms)
 * @returns {Promise<void>} Resolves when animation completes
 */
export function scrambleText(element, finalText, duration = 800) {
  return new Promise((resolve) => {
    const originalText = finalText;
    const length = originalText.length;
    let iteration = 0;
    const totalSteps = 20;
    const intervalTime = duration / totalSteps;

    const interval = setInterval(() => {
      element.textContent = originalText
        .split('')
        .map((char, index) => {
          if (char === ' ') return ' ';
          if (index < iteration) {
            return originalText[index];
          }
          return CYBER_CHARS[Math.floor(Math.random() * CYBER_CHARS.length)];
        })
        .join('');

      iteration += length / totalSteps;

      if (iteration >= length) {
        clearInterval(interval);
        element.textContent = originalText;
        resolve();
      }
    }, intervalTime);
  });
}
