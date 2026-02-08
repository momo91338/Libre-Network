// frontend/src/App.jsx
import React, { useState } from "react";
import { BrowserRouter as Router, Routes, Route, Link } from "react-router-dom";


import Wallet from "./components/Wallet.jsx";
import Mining from "./components/Mining.jsx";
import TermsOfUse from "./components/TermsOfUse.jsx";
import CreateAccount from "./components/CreateAccount.jsx";



export default function App() {
  const [termsAccepted, setTermsAccepted] = useState(false);

  return (
    <>
      {!termsAccepted && <TermsOfUse onAccept={setTermsAccepted} />}

      {termsAccepted && (
        <Router>
          <div style={{ padding: 20 }}>
            <nav style={{ marginBottom: 20 }}>
              <Link to="/" style={{ marginRight: 15 }}>المحفظة</Link>
              <Link to="/mining">التعدين</Link>
            <Link to="/CreateAccount">MOMO</Link>
            

            

</nav>

            <Routes>
              <Route path="/" element={<Wallet />} />
              <Route path="/mining" element={<Mining />} />
      <Route path="/CreateAccount " element={<CreateAccount  />} />
  
    </Routes>
          </div>
        </Router>
      )}
    </>
  );
}
