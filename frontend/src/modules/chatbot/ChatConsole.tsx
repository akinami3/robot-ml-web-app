import React, { useState } from "react";

import TabLayout from "../../shared/layouts/TabLayout";

const ChatConsole: React.FC = () => {
  const [question, setQuestion] = useState("");

  return (
    <TabLayout title="RAG Chatbot">
      <div className="space-y-4">
        <textarea
          className="w-full min-h-[120px] bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-slate-100"
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          placeholder="質問を入力してください"
        />
        <button className="px-4 py-2 bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 rounded-md">
          Ask
        </button>
      </div>
    </TabLayout>
  );
};

export default ChatConsole;
