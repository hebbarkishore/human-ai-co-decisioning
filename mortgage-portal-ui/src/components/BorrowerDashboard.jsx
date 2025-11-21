
import React, { useEffect, useState } from 'react';
import axios from 'axios';

function BorrowerDashboard({ user, onSwitch }) {
  const [borrowerData, setBorrowerData] = useState(null);
  const [file, setFile] = useState(null);

  const fetchBorrower = async () => {
    const res = await axios.get(`http://localhost:8001/borrower-helper-service/borrower/${user.id}`);
    setBorrowerData(res.data);
  };

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  const handleSubmit = async () => {
    const formData = new FormData();
    formData.append("file", file);
    await axios.post(`http://localhost:8001/borrower-helper-service/borrower/${user.email}/check-eligibility`, formData);
    setFile(null);
    fetchBorrower();
  };

  useEffect(() => {
    fetchBorrower();
  }, []);

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-4">
        <h1 className="text-xl font-bold">Welcome, {user.full_name}</h1>
        <button className="bg-blue-600 text-white px-4 py-2 rounded" onClick={onSwitch}>Switch as Underwriter</button>
      </div>

      {borrowerData && (
        <table className="w-full mt-4 border">
          <thead className="bg-gray-200">
            <tr>
              <th className="p-2 text-left">Name</th>
              <th className="p-2 text-left">Email</th>
              <th className="p-2 text-left">Status</th>
              <th className="p-2 text-left">Action</th>
            </tr>
          </thead>
          <tbody>
            <tr className="border-t">
              <td className="p-2">{borrowerData.full_name}</td>
              <td className="p-2">{borrowerData.email}</td>
              <td className="p-2">{borrowerData.status || "—"}</td>
              <td className="p-2">
                {borrowerData.status === null && (
                  <div className="flex gap-2">
                    <input type="file" onChange={handleFileChange} className="border" />
                    <button className="bg-green-500 text-white px-2 py-1 rounded" onClick={handleSubmit}>
                      Submit
                    </button>
                  </div>
                )}
              </td>
            </tr>
          </tbody>
        </table>
      )}
    </div>
  );
}

export default BorrowerDashboard;
