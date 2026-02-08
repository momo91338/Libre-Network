import React, { useState } from 'react'
import axios from 'axios'

export default function CreateAccount() {
  const [keys, setKeys] = useState(null)
  const [error, setError] = useState(null)

  const handleCreate = async () => {
    try {
      const res = await axios.post('http://localhost:4000/api/accounts/create')
      setKeys(res.data)
      setError(null)
    } catch {
      setError('حدث خطأ أثناء إنشاء الحساب')
    }
  }

  return (
    <div>
      <h2>إنشاء حساب جديد</h2>
      <button onClick={handleCreate}>إنشاء حساب</button>

      {error && <p style={{ color: 'red' }}>{error}</p>}

      {keys && (
        <div>
          <h3>مفاتيح الحساب:</h3>
          <p><strong>المفتاح العام:</strong><br />{keys.publicKey}</p>
          <p><strong>المفتاح الخاص:</strong><br /><code>{keys.privateKey}</code></p>
          <p style={{ color: 'orange' }}>
            احفظ المفتاح الخاص بأمان ولا تشاركه مع أي أحد!
          </p>
        </div>
      )}
    </div>
  )
}
