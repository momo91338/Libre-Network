// frontend/src/utils/helpers.js

// توليد نوسى عشوائي بين 0 و max
export function generateNonce(max = 1000000) {
  return Math.floor(Math.random() * max);
}

// اختيار n عنصر عشوائي من مصفوفة (بدون تكرار)
export function chooseRandom(items, n) {
  if (n >= items.length) return [...items];
  const result = [];
  const taken = new Set();
  while (result.length < n) {
    const index = Math.floor(Math.random() * items.length);
    if (!taken.has(index)) {
      taken.add(index);
      result.push(items[index]);
    }
  }
  return result;
}

// دالة بسيطة لتوليد هاش (يمكن استبدالها بـ SHA256 حقيقي في الباكند)
export function simpleHash(str) {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    hash = (hash << 5) - hash + str.charCodeAt(i);
    hash |= 0; // تحويل إلى 32-بت integer
  }
  return hash.toString(16);
}
