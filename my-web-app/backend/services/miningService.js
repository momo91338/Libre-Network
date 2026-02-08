// backend/services/miningService.js
const MinerList = require('../models/MinerList');
const Update = require('../models/Update');
const { chooseRandom, simpleHash } = require('../../frontend/src/utils/helpers'); // يمكنك نقل الدوال لموديل مشترك لاحقاً

// اختيار 100 معدن عشوائي من قائمة المعدنين بناء على الهاش
async function selectSigners(minerListNumber, updateHash) {
  const minerList = await MinerList.findOne({ listNumber: minerListNumber });
  if (!minerList) throw new Error('قائمة المعدنين غير موجودة');

  // نستخدم دالة اختيار عشوائي (تستقبل القائمة والعدد المطلوب)
  return chooseRandom(minerList.miners, 100);
}

// توليد توقيع مجمع (اختصار - في الواقع يحتاج لتشفير فعلي)
function generateAggregateSignature(signers, updateHash) {
  // نجمع عناوين المعدنين والتحديث والهاش لنحصل على توقيع مجمع مبدئي
  const data = signers.join('') + updateHash;
  return simpleHash(data);
}

// تحقق من صحة التوقيع المجمع (تأكد أن التوقيع مطابق)
function verifyAggregateSignature(aggregateSignature, signers, updateHash) {
  const expected = generateAggregateSignature(signers, updateHash);
  return expected === aggregateSignature;
}

module.exports = {
  selectSigners,
  generateAggregateSignature,
  verifyAggregateSignature
};
