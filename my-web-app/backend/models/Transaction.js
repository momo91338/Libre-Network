// backend/models/Transaction.js
const mongoose = require('mongoose');

const TransactionSchema = new mongoose.Schema({
  type: { 
    type: String, 
    enum: ['TRANSFER', 'INCREASE_MINING_AGE', 'CREATE_ACCOUNT', 'CHANGE_OWNERSHIP', 'ENTER_MINING_POOL'],
    required: true
  },
  from: { type: String, required: true }, // العنوان المرسل
  to: { type: String }, // العنوان المستلم (إن وجد)
  amount: { type: Number, default: 0 }, // المبلغ أو النقاط حسب نوع المعاملة
  fee: { type: Number, required: true },
  nonce: { type: Number, required: true },
  timestamp: { type: Date, default: Date.now }
});

module.exports = mongoose.model('Transaction', TransactionSchema);
