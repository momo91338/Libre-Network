// backend/routes/transactions.js
const express = require('express');
const router = express.Router();

const Transaction = require('../models/Transaction');

// جلب جميع المعاملات الخاصة بمستخدم معين
router.get('/:address', async (req, res) => {
  try {
    const { address } = req.params;
    const transactions = await Transaction.find({ from: address }).sort({ timestamp: -1 });
    res.json(transactions);
  } catch (error) {
    res.status(500).json({ message: 'فشل في جلب المعاملات' });
  }
});

// إضافة معاملة جديدة إلى مجمع المعاملات
router.post('/', async (req, res) => {
  try {
    const txData = req.body;
    const transaction = new Transaction(txData);
    await transaction.save();
    res.status(201).json(transaction);
  } catch (error) {
    res.status(400).json({ message: 'فشل في إضافة المعاملة' });
  }
});

module.exports = router;
