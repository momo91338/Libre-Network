// frontend/src/components/TermsOfUse.jsx
import React, { useState, useEffect } from 'react';

export default function TermsOfUse({ onAccept }) {
  const [accepted, setAccepted] = useState(false);

  useEffect(() => {
    const savedAcceptance = localStorage.getItem('termsAccepted');
    if (savedAcceptance === 'true') {
      setAccepted(true);
      onAccept(true);
    }
  }, [onAccept]);

  const handleAccept = () => {
    setAccepted(true);
    localStorage.setItem('termsAccepted', 'true');
    onAccept(true);
  };

  if (accepted) return null;

  return (
    <div style={{
      position: 'fixed',
      top: 0, left: 0, right: 0, bottom: 0,
      backgroundColor: 'rgba(0,0,0,0.6)',
      display: 'flex', justifyContent: 'center', alignItems: 'center',
      zIndex: 1000,
      padding: 20,
    }}>
      <div style={{
        backgroundColor: 'white',
        borderRadius: 8,
        maxWidth: 600,
        padding: 20,
        maxHeight: '80vh',
        overflowY: 'auto',
      }}>
        <h2>شروط الاستخدام</h2>
        <p>
          يرجى قراءة الشروط التالية بعناية قبل استخدام المحفظة.
          <br /><br />
          - إذا لم تقم بأي معاملة باستخدام حسابك لمدة 200,000,000 تحديث، سيتم حذف حسابك وحرق رصيدك.
          <br />
          - بالضغط على "أوافق"، فإنك توافق على هذه الشروط وتتحمل مسؤولية استخدام المحفظة.
        </p>
        <button
          onClick={handleAccept}
          style={{ marginTop: 20, padding: '10px 20px', cursor: 'pointer' }}
        >
          أوافق
        </button>
      </div>
    </div>
  );
}
