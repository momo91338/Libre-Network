// frontend/src/components/Wallet.jsx
import React, { useEffect, useState } from 'react';
import { getUserTransactions, addTransaction } from '../api/apiClient';
import TransactionForm from './TransactionForm';

export default function Wallet({ userAddress, usersDB, setUsersDB }) {
  const [balance, setBalance] = useState(0);
  const [transactions, setTransactions] = useState([]);
  const [localNonce, setLocalNonce] = useState(0);

  // تحديث الرصيد بناءً على usersDB
  useEffect(() => {
    if (usersDB && usersDB[userAddress]) {
      setBalance(usersDB[userAddress].balance);
      setLocalNonce(usersDB[userAddress].nonce || 0);
    }
  }, [usersDB, userAddress]);

  // جلب معاملات المستخدم
  useEffect(() => {
    if (!userAddress) return;
    async function fetchTransactions() {
      const txs = await getUserTransactions(userAddress);
      setTransactions(txs);
    }
    fetchTransactions();
  }, [userAddress]);

  // إرسال معاملة جديدة
  const handleSendTransaction = async (txData) => {
    try {
      const newTx = {
        ...txData,
        from: userAddress,
        nonce: localNonce + 1,
        timestamp: Date.now(),
      };
      await addTransaction(newTx);
      setLocalNonce((n) => n + 1);
      alert('تم إرسال المعاملة');
    } catch (error) {
      alert('خطأ في إرسال المعاملة: ' + error.message);
    }
  };

  return (
    <div className="wallet-container" style={{ padding: '20px', maxWidth: '600px', margin: 'auto' }}>
      <h2>محفظة المستخدم</h2>
      <p><strong>العنوان:</strong> {userAddress}</p>
      <p><strong>الرصيد:</strong> {balance.toFixed(6)} LBRC</p>

      <TransactionForm onSend={handleSendTransaction} localNonce={localNonce} />

      <h3>المعاملات الأخيرة</h3>
      <ul style={{ maxHeight: '300px', overflowY: 'auto', listStyle: 'none', padding: 0 }}>
        {transactions.length === 0 && <li>لا توجد معاملات</li>}
        {transactions.map((tx) => (
          <li key={tx._id} style={{ borderBottom: '1px solid #ddd', padding: '8px 0' }}>
            <div>النوع: {tx.type}</div>
            <div>إلى: {tx.to || '-'}</div>
            <div>المبلغ: {tx.amount || 0}</div>
            <div>الرسوم: {tx.fee}</div>
            <div>النوسى: {tx.nonce}</div>
            <div>التاريخ: {new Date(tx.timestamp).toLocaleString()}</div>
          </li>
        ))}
      </ul>
    </div>
  );
}
