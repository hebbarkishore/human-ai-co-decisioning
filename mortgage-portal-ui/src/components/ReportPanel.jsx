import React from 'react';

function ReportPanel({ report, onClose }) {
  if (!report) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex justify-center items-center z-50">
      <div className="bg-white p-6 rounded-lg shadow-xl max-w-lg w-full relative">
        <button
          onClick={onClose}
          className="absolute top-2 right-2 text-gray-600 hover:text-black"
        >
          ✕
        </button>
        <h2 className="text-lg font-bold mb-4">Detail Explanation from each module</h2>
        <p><strong>Rule Explanation:</strong> {report.explanation.rule_explanation}</p>
        <p><strong>ML Explanation:</strong> {report.explanation.ml_explanation}</p>
        <p><strong>Fairness Explanation:</strong> {report.explanation.fairness_explanation}</p>
      </div>
    </div>
  );
}

export default ReportPanel;