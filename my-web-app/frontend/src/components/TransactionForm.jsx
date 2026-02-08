// frontend/src/components/TransactionForm.jsx
import React, { useState } from 'react';

export default function TransactionForm({ onSend, localNonce }) {
  const [type, setType] = useState('TRANSFER');
  const [to, setTo] = useState('');
  const [amount, setAmount] = useState('');
  const [fee, setFee] = useState('');
  const [message, setMessage] = useState('');

  const resetForm = () => {
    setTo('');
    setAmount('');
    setFee('');
    setMessage('');
  };

  const handleSubmit = (e) => {
    e.preventDefault();

    let txData = {
      type,
      fee: parseFloat(fee),
    };

    if (type === 'TRANSFER') {
      if (!to) return alert('يرجى إدخال عنوان المستلم');
      if (!amount || isNaN(amount) || Number(amount) <= 0) return alert('يرجى إدخال مبلغ صحيح');
      txData = { ...txData, to, amount: Number(amount) };
    } else if (type === 'INCREASE_MINING_AGE') {
      if (!amount || isNaN(amount) || Number(amount) <= 0) return alert('يرجى إدخال نقاط عمر التعدين');
      txData = { ...txData, amount: Number(amount) };
    } else if (type === 'CREATE_ACCOUNT' || type === 'CHANGE_OWNERSHIP' || type === 'ENTER_MINING_POOL') {
      // لا حاجة لمزيد من الحقول
    }

    onSend(txData);
    resetForm();
  };

  return (
    <form onSubmit={handleSubmit} style={{ marginBottom: '20px', border: '1px solid #ddd', padding: '15px', borderRadius: '8px' }}>
      <h3>إرسال معاملة جديدة</h3>

      <label>نوع المعاملة:</label>
      <select value={type} onChange={(e) => setType(e.target.value)} style={{ width: '100%', marginBottom: '10px' }}>
        <option value="TRANSFER">تحويل من شخص لشخص</option>
        <option value="INCREASE_MINING_AGE">تزويد العمر التعديني</option>
        <option value="CREATE_ACCOUNT">إنشاء حساب جديد</option>
        <option value="CHANGE_OWNERSHIP">تغيير ملكية الحساب</option>
        <option value="ENTER_MINING_POOL">دخول مجمع المعدنين</option>
      </select>

      {(type === 'TRANSFER') && (
        <>
          <label>العنوان المستلم:</label>
          <input
            type="text"
            value={to}
            onChange={(e) => setTo(e.target.value)}
            placeholder="أدخل عنوان المستلم"
            required
            style={{ width: '100%', marginBottom: '10px' }}
          />
          <label>المبلغ:</label>
          <input
            type="number"
            step="0.000001"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
            placeholder="أدخل المبلغ"
            required
            style={{ width: '100%', marginBottom: '10px' }}
          />
        </>
      )}

      {(type === 'INCREASE_MINING_AGE') && (
        <>
          <label>نقاط العمر التعديني:</label>
          <input
            type="number"
            step="0.000001"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
            placeholder="أدخل نقاط العمر"
            required
            style={{ width: '100%', marginBottom: '10px' }}
          />
        </>
      )}

      <label>الرسوم (الفائدة):</label>
      <input
        type="number"
        step="0.000001"
        value={fee}
        onChange={(e) => setFee(e.target.value)}
        placeholder="أدخل رسوم المعاملة"
        required
        style={{ width: '100%', marginBottom: '10px' }}
      />

      <button type="submit" style={{ padding: '10px 15px', cursor: 'pointer' }}>إرسال المعاملة</button>

      {message && <p>{message}</p>}
    </form>
  );
}
