
import React from 'react';

function LetterEditor({ letter, setLetter, updateLetter }) {
  return (
    <div className="mt-6 p-4 border bg-white shadow">
      <h2 className="text-lg font-bold mb-2">Generated Letter</h2>
      <textarea
        className="w-full h-60 border p-2"
        value={letter.letter_text}
        onChange={(e)=>setLetter({ ...letter, letter_text: e.target.value })}
      />
      <button className="mt-3 bg-green-600 text-white p-2" onClick={updateLetter}>
        Update Letter
      </button>
    </div>
  );
}

export default LetterEditor;
