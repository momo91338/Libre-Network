// frontend/src/components/Mining.jsx
import React, { useState, useEffect } from 'react';
import { createUpdate, enterMiningPool, getLatestUpdate } from '../api/apiClient';

export default function Mining({ userAddress }) {
  const [nonce, setNonce] = useState(0);
  const [isMining, setIsMining] = useState(false);
  const [status, setStatus] = useState('');
  const [miningAge, setMiningAge] = useState(0);

  // جلب آخر تحديث للنوسى
  useEffect(() => {
    async function fetchLatest() {
      const latest = await getLatestUpdate();
      setNonce(latest ? latest.nonce : 0);
    }
    fetchLatest();
  }, []);

  // بدء التعدين (ببساطة توليد تحديث مع نوسى)
  const startMining = async () => {
    if (!userAddress) {
      alert('يرجى تسجيل الدخول أولاً');
      return;
    }
    setIsMining(true);
    setStatus('جاري التعدين...');

    // جرب زيادة النوسى حتى تجد "تحديث مقبول"
    let currentNonce = nonce;
    let newUpdate = null;
    while (isMining) {
      currentNonce++;
      try {
        newUpdate = await createUpdate(userAddress, currentNonce);
        if (newUpdate) {
          setStatus(`تم إنشاء تحديث رقم ${newUpdate.updateNumber} بنجاح!`);
          setNonce(currentNonce);
          break;
        }
      } catch (err) {
        // يمكن وضع شروط قبول حسب صعوبة
      }
    }
    setIsMining(false);
  };

  // دخول مجمع المعدنين
  const handleEnterMiningPool = async () => {
    if (miningAge <= 0) {
      alert('العمر التعديني = 0 لا يمكنك الدخول');
      return;
    }
    try {
      await enterMiningPool(userAddress);
      alert('تم دخول مجمع المعدنين');
    } catch (error) {
      alert('خطأ في دخول مجمع المعدنين: ' + error.message);
    }
  };

  return (
    <div style={{ padding: 20, maxWidth: 600, margin: 'auto' }}>
      <h2>صفحة التعدين</h2>
      <p>النوسى الحالي: {nonce}</p>
      <button onClick={startMining} disabled={isMining}>
        {isMining ? 'جار التعدين...' : 'بدء التعدين'}
      </button>
      <p>{status}</p>
      <hr />
      <button onClick={handleEnterMiningPool}>دخول مجمع المعدنين</button>
    </div>
  );
}
