// frontend/src/api/apiClient.js

const API_BASE_URL = 'http://localhost:5000/api'; // غيّر حسب إعداد السيرفر

// جلب معاملات مستخدم معين
export async function getUserTransactions(address) {
  const res = await fetch(`${API_BASE_URL}/transactions/${address}`);
  if (!res.ok) throw new Error('فشل في جلب المعاملات');
  return res.json();
}

// إضافة معاملة جديدة إلى مجمع المعاملات
export async function addTransaction(txData) {
  const res = await fetch(`${API_BASE_URL}/transactions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(txData),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.message || 'خطأ في إرسال المعاملة');
  }
  return res.json();
}

// جلب آخر تحديث (مثلاً للنوسى أو حالة الشبكة)
export async function getLatestUpdate() {
  const res = await fetch(`${API_BASE_URL}/updates/latest`);
  if (!res.ok) throw new Error('فشل في جلب آخر تحديث');
  return res.json();
}

// إنشاء تحديث جديد (يتم التعدين)
export async function createUpdate(userAddress, nonce) {
  const res = await fetch(`${API_BASE_URL}/updates`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ userAddress, nonce }),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.message || 'خطأ في إنشاء التحديث');
  }
  return res.json();
}

// دخول مجمع المعدنين
export async function enterMiningPool(userAddress) {
  const res = await fetch(`${API_BASE_URL}/miners/enter`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ userAddress }),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.message || 'خطأ في دخول مجمع المعدنين');
  }
  return res.json();
}

// جلب قائمة المعدنين الحالية
export async function getMinerList() {
  const res = await fetch(`${API_BASE_URL}/miners`);
  if (!res.ok) throw new Error('فشل في جلب قائمة المعدنين');
  return res.json();
}
