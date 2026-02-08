// backend/models/MinerList.js
const mongoose = require('mongoose');

const MinerListSchema = new mongoose.Schema({
  listNumber: { type: Number, required: true, unique: true },
  miners: [{ type: String, required: true }], // عناوين المعدنين
  createdAt: { type: Date, default: Date.now }
});

module.exports = mongoose.model('MinerList', MinerListSchema);
