import React from 'react';

function BorrowerTable({ borrowers, onExplanationClick, onChangeDecisionClick }) {
  return (
    <table className="mt-6 w-full border">
      <thead>
        <tr className="bg-gray-200">
          <th className="border p-2">Name</th>
          <th className="border p-2">Email</th>
          <th className="border p-2">Status</th>
          <th className="border p-2">Action</th>
        </tr>
      </thead>
      <tbody>
        {borrowers.map(b => (
          <tr key={b.id}>
            <td className="border p-2">{b.full_name}</td>
            <td className="border p-2">{b.email}</td>
            <td className="border p-2">{b.status}</td>
            <td className="border p-2 flex gap-2">
              {(b.status === 'approved' || b.status === 'rejected' || b.status ===  'pending_conflict') && (
                <>
                  <button
                    className="bg-blue-500 text-white p-1 rounded"
                    onClick={() => onExplanationClick(b)}
                  >
                    Explanation
                  </button>
                  <button
                    className="bg-green-500 text-white p-1 rounded"
                    onClick={() => onChangeDecisionClick(b)}
                  >
                    Change Decision
                  </button>
                </>
              )}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

export default BorrowerTable;