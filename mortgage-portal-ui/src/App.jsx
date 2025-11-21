
import React, { useState } from 'react';
import LoginPage from './components/LoginPage';
import UnderwriterDashboard from './components/UnderwriterDashboard';
import BorrowerDashboard from './components/BorrowerDashboard';

function App() {
  const [user, setUser] = useState(null);

  const handleLogout = () => setUser(null);

  if (!user) return <LoginPage onLogin={setUser} />;

  if (user.role === 'underwriter') {
    return <UnderwriterDashboard user={user} onSwitch={() => setUser(null)} />;
  } else if (user.role === 'borrower') {
    return <BorrowerDashboard user={user} onSwitch={() => setUser(null)} />;
  } else {
    return <div>Invalid role</div>;
  }
}

export default App;
