// backend/models/Update.js
const mongoose = require('mongoose');

const UpdateSchema = new mongoose.Schema({
  updateNumber: { type: Number, required: true, unique: true },
  minerListNumber: { type: Number, required: true },
  nonce: { type: Number, required: true },
  transactions: { type: Array, required: true },
  stateHash: { type: String, required: true },
  aggregateSignature: { type: String, default: null }, // التوقيع المجمع من 100 معدن
  createdAt: { type: Date, default: Date.now }
});

module.exports = mongoose.model('Update', UpdateSchema);
