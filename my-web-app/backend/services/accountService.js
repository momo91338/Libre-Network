const crypto = require('crypto')

function generateKeyPair() {
  const { publicKey, privateKey } = crypto.generateKeyPairSync('ec', {
    namedCurve: 'secp256k1',
    publicKeyEncoding: { type: 'spki', format: 'pem' },
    privateKeyEncoding: { type: 'pkcs8', format: 'pem' },
  })
  return { publicKey, privateKey }
}

async function createAccount() {
  // توليد المفاتيح
  const keys = generateKeyPair()

  // هنا يمكن تخزين المفتاح العام في قاعدة البيانات كمستخدم جديد
  // مثلا:
  // await UserModel.create({ publicKey: keys.publicKey, balance: 0, ... })

  // لكن المفتاح الخاص لا يُخزن في السيرفر، بل يُرسل للعميل ليحفظه

  return keys
}

module.exports = { createAccount }
