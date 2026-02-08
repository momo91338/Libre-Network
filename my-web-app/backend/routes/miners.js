// backend/routes/miners.js
const express = require('express');
const router = express.Router();

const MinerList = require('../models/MinerList');
const User = require('../models/User'); // نفترض وجود موديل المستخدمين

// جلب آخر قائمة معدنين
router.get('/latest', async (req, res) => {
  try {
    const latestList = await MinerList.findOne().sort({ listNumber: -1 });
    res.json(latestList);
  } catch (error) {
    res.status(500).json({ message: 'خطأ في جلب قائمة المعدنين' });
  }
});

// إضافة مستخدم إلى مجمع المعدنين (يتم استخدام معاملة من الواجهة)
router.post('/enter-pool', async (req, res) => {
  try {
    const { userAddress } = req.body;
    const user = await User.findOne({ address: userAddress });
    if (!user) return res.status(400).json({ message: 'المستخدم غير موجود' });

    // هنا تضع منطق إضافة المستخدم إلى مجمع المعدنين في قاعدة البيانات
    // ...

    res.json({ message: 'تم إضافة المستخدم إلى مجمع المعدنين' });
  } catch (error) {
    res.status(500).json({ message: 'خطأ في إضافة المستخدم إلى مجمع المعدنين' });
  }
});

module.exports = router;
