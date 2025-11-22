import React from 'react';

function ReportPanel({ report, onClose }) {
  if (!report || !report.explanation) return null;

  const rule = report.explanation.rule_explanation || {};
  const ml = report.explanation.ml_explanation || {};
  const fairness = report.explanation.fairness_explanation || "No fairness explanation available.";

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex justify-center items-center z-50">
      <div className="bg-white p-6 rounded-lg shadow-xl max-w-lg w-full relative">
        <button
          onClick={onClose}
          className="absolute top-2 right-2 text-gray-600 hover:text-black"
        >
          ✕
        </button>
        <h2 className="text-lg font-bold mb-4">Detail Explanation from Each Module</h2>

        {rule && (rule.passed_cases || rule.failed_cases || rule.result) && (
          <div className="mb-4">
            <h3 className="font-semibold">Rule Explanation:</h3>
            {rule.passed_cases && <p><strong>Passed Cases:</strong> {rule.passed_cases}</p>}
            {rule.failed_cases && <p><strong>Failed Cases:</strong> {rule.failed_cases}</p>}
            {rule.result && <p><strong>Result:</strong> {rule.result}</p>}
          </div>
        )}

        {ml && (ml.passed_cases || ml.failed_cases || ml.result) && (
          <div className="mb-4">
            <h3 className="font-semibold">ML Explanation:</h3>
            {ml.passed_cases && <p><strong>Passed Cases:</strong> {ml.passed_cases}</p>}
            {ml.failed_cases && <p><strong>Failed Cases:</strong> {ml.failed_cases}</p>}
            {ml.result && <p><strong>Result:</strong> {ml.result}</p>}
          </div>
        )}

        <div>
          <h3 className="font-semibold">Fairness Explanation:</h3>
          <p>{fairness}</p>
        </div>
      </div>
    </div>
  );
}

export default ReportPanel;