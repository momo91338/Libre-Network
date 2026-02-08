const express = require('express')
const router = express.Router()
const { createAccount } = require('../services/accountService')

router.post('/create', async (req, res) => {
  try {
    const keys = await createAccount()
    res.json({
      message: 'تم إنشاء الحساب بنجاح',
      publicKey: keys.publicKey,
      privateKey: keys.privateKey, // أرسلها للعميل ليحفظها بأمان
    })
  } catch (error) {
    res.status(500).json({ error: 'فشل إنشاء الحساب' })
  }
})

module.exports = router
