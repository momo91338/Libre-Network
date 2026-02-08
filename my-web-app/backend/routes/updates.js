// backend/routes/updates.js
const express = require('express');
const router = express.Router();

const Update = require('../models/Update');
const miningService = require('../services/miningService');
const transactionService = require('../services/transactionService');

// جلب آخر تحديث
router.get('/latest', async (req, res) => {
  try {
    const latestUpdate = await Update.findOne().sort({ updateNumber: -1 });
    res.json(latestUpdate);
  } catch (error) {
    res.status(500).json({ message: 'خطأ في جلب آخر تحديث' });
  }
});

// إنشاء تحديث جديد (عملية التعدين)
router.post('/', async (req, res) => {
  try {
    const { userAddress, nonce } = req.body;
    
    // جلب آخر تحديث لمعرفة رقم التحديث القادم
    const latestUpdate = await Update.findOne().sort({ updateNumber: -1 });
    const nextUpdateNumber = latestUpdate ? latestUpdate.updateNumber + 1 : 1;

    // جلب قائمة المعدنين الحالية
    const minerList = await require('../models/MinerList').findOne().sort({ listNumber: -1 });
    if (!minerList) return res.status(400).json({ message: 'لا توجد قائمة معدنين حالية' });

    // تجميع المعاملات من مجمع المعاملات (يجب تنفيذ ذلك - هنا افتراضيا [])
    const transactions = []; // TODO: جلب المعاملات من مجمع المعاملات

    // إضافة معاملة مكافأة التعدين
    transactions.push({
      type: 'REWARD',
      from: 'SYSTEM',
      to: userAddress,
      amount: 100,
      fee: 0,
      nonce: nonce,
      timestamp: Date.now(),
    });

    // تحديث الحالة وتنفيذ المعاملات (ينبغي استخدام transactionService)

    // توليد هاش جديد للتحديث (يمكن استخدام simpleHash)
    const { simpleHash } = require('../../frontend/src/utils/helpers');
    const stateHash = simpleHash(JSON.stringify(transactions) + nonce);

    // إنشاء التحديث وحفظه
    const newUpdate = new Update({
      updateNumber: nextUpdateNumber,
      minerListNumber: minerList.listNumber,
      nonce,
      transactions,
      stateHash,
      aggregateSignature: null,
    });

    await newUpdate.save();

    res.json(newUpdate);
  } catch (error) {
    console.error(error);
    res.status(500).json({ message: 'خطأ في إنشاء التحديث' });
  }
});

module.exports = router;
