// src/components/DecisionModal.jsx
import React, { useState } from 'react';

function DecisionModal({ borrowerId, underwriterId, onClose, onSubmit }) {
  const [newStatus, setNewStatus] = useState("");

  const handleSubmit = () => {
    if (newStatus) {
      onSubmit({ borrower_id: borrowerId, underwriter_id: underwriterId, new_status: newStatus });
    }
  };

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 flex justify-center items-center z-50">
      <div className="bg-white p-6 rounded shadow w-96">
        <h2 className="text-xl font-bold mb-4">Please select the new status</h2>

        <div className="mb-4">
          <label className="block mb-2">
            <input
              type="radio"
              name="status"
              value="approved"
              onChange={() => setNewStatus("approved")}
              className="mr-2"
            />
            Approve
          </label>
          <label className="block">
            <input
              type="radio"
              name="status"
              value="rejected"
              onChange={() => setNewStatus("rejected")}
              className="mr-2"
            />
            Reject
          </label>
        </div>

        <div className="flex justify-end gap-2">
          <button onClick={onClose} className="bg-gray-400 text-white px-4 py-2 rounded">Cancel</button>
          <button onClick={handleSubmit} className="bg-blue-600 text-white px-4 py-2 rounded">Submit</button>
        </div>
      </div>
    </div>
  );
}

export default DecisionModal;