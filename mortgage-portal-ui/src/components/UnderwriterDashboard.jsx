import React, { useEffect, useState } from 'react';
import axios from 'axios';
import BorrowerTable from './BorrowerTable';
import ReportPanel from './ReportPanel';
import DecisionModal from './DecisionModal';


function UnderwriterDashboard({ user, onSwitch }) {
  const [borrowers, setBorrowers] = useState([]);
  const [selected, setSelected] = useState(null);
  const [report, setReport] = useState(null);
  const [letter, setLetter] = useState(null);
  const [showDecisionModal, setShowDecisionModal] = useState(false);

  const fetchBorrowers = async () => {
    const res = await axios.get('http://localhost:8001/borrower-helper-service/borrowers');
    setBorrowers(res.data);
  };

  useEffect(() => {
    fetchBorrowers();
  }, []);

  const loadDetails = async (b) => {
    setSelected(b);
    const rep = await axios.get(`http://localhost:8006/underwriter-helper-service/application-explanation/borrower/${b.id}`);
    setReport(rep.data);
  };

  const handleDecisionSubmit = async (payload) => {
    await axios.post("http://localhost:8006/underwriter-helper-service/manual-decision-update", payload);
    setShowDecisionModal(false);
    fetchBorrowers(); // Refresh table
  };

  const generateLetter = async () => {
    const res = await axios.post(`http://localhost:8010/underwriter/generate_letter/${selected.id}`);
    setLetter(res.data);
  };

  const updateLetter = async () => {
    await axios.put(`http://localhost:8010/underwriter/update_letter/${letter.letter_id}`, {
      letter_text: letter.letter_text
    });
    alert("Updated!");
  };

  return (
    <div className="p-6">
      <div className="flex justify-between items-center">
      <h1 className="text-xl font-bold">Welcome, {user.full_name}</h1>
      <button className="bg-blue-600 text-white px-4 py-2 rounded" onClick={onSwitch}>Switch as Borrower</button>
    </div>

      <BorrowerTable
        borrowers={borrowers}
        onExplanationClick={loadDetails}
        onChangeDecisionClick={(b) => {
          setSelected(b);
          setShowDecisionModal(true);
        }}
      />

      {report && <ReportPanel report={report} onClose={() => setReport(null)}/>}

      {showDecisionModal && selected && (
        <DecisionModal
          borrowerId={selected.id}
          underwriterId={user.id}
          onClose={() => setShowDecisionModal(false)}
          onSubmit={handleDecisionSubmit}
        />
      )}
    </div>
  );
}
export default UnderwriterDashboard;