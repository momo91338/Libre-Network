const mongoose = require('mongoose')

const UserSchema = new mongoose.Schema(
  {
    address: {
      type: String,
      required: true,
      unique: true
    },
    balance: {
      type: Number,
      default: 0
    },
    nonce: {
      type: Number,
      default: 0
    },
    createdAt: {
      type: Date,
      default: Date.now
    }
  },
  { versionKey: false }
)

module.exports = mongoose.model('User', UserSchema)
