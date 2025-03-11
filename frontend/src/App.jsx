import React, { useState } from "react";
import axios from "axios";
import MonacoEditor from "@monaco-editor/react";
import Tree from "react-d3-tree";

function App() {
  const [code, setCode] = useState("// Type your C++ code here...");
  const [tokens, setTokens] = useState([]);
  const [tree, setTree] = useState({});

  const analyzeCode = async () => {
    try {
      const response = await axios.post("http://127.0.0.1:8000/tokenize", {
        code,
      });
      setTokens(response.data.tokens);
    } catch (error) {
      console.error("Error analyzing code:", error);
    }
  };

  const parseCode = async () => {
    try {
      const response = await axios.post("http://127.0.0.1:8000/parse", {
        code,
      });
      console.log(response.data.parse_tree);
      setTree(response.data.parse_tree);
    } catch (error) {
      console.error("Error analyzing code:", error);
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white flex flex-col items-center p-6">
      <h1 className="text-3xl font-bold mb-4">C++ Visual Compiler</h1>
      {/* Monaco Editor */}
      <div className="w-full max-w-3xl shadow-md rounded-lg overflow-hidden">
        <MonacoEditor
          height="350px"
          theme="vs-dark"
          language="cpp"
          value={code}
          options={{
            fontSize: 16,
            minimap: { enabled: false },
            wordWrap: "on",
            padding: { top: 10, bottom: 10 },
          }}
          onChange={(value) => setCode(value)}
        />
      </div>
      {/* Button */}
      <div className="w-full max-w-3xl flex gap-4">
        <button
          onClick={analyzeCode}
          className="w-1/2 mt-4 bg-blue-500 px-4 py-2 rounded hover:bg-blue-700 transition"
        >
          Analyze Code
        </button>
        <button
          onClick={parseCode}
          className="w-1/2 mt-4 bg-blue-500 px-4 py-2 rounded hover:bg-blue-700 transition"
        >
          Parse Code
        </button>
      </div>
      {/* Tokens Display */}
      {tokens.length > 0 && (
        <div className="mt-6 w-full max-w-3xl p-4 bg-gray-800 rounded shadow-md">
          <h2 className="text-xl font-semibold mb-2">Tokens</h2>
          <table className="w-full border-collapse border border-gray-700">
            <thead>
              <tr className="bg-gray-700">
                <th className="border border-gray-600 p-2">Type</th>
                <th className="border border-gray-600 p-2">Value</th>
              </tr>
            </thead>
            <tbody>
              {tokens.map((token, index) => (
                <tr key={index} className="border border-gray-700">
                  <td className="border border-gray-600 p-2">{token.type}</td>
                  <td className="border border-gray-600 p-2">{token.value}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {Object.keys(tree).length > 0 && (
  <div className="mt-6 w-full max-w-3xl p-4 bg-gray-800 rounded shadow-md">
    <h2 className="text-xl font-semibold mb-2">Parse Tree</h2>
    <div className="border border-gray-700" style={{ height: "400px" }}>
      <Tree
        data={tree}
        orientation="vertical"
        translate={{ x: 300, y: 50 }} // Centers the tree horizontally, adds top margin
        zoomable={false}
        styles={{
          links: {
            stroke: "#ffffff", // White links
            strokeWidth: 2,   // Thicker lines for visibility
          },
        }}
        renderCustomNodeElement={({ nodeDatum }) => (
          <g>
            <circle
              r={15} // Slightly larger node size
              fill="#777777" // White nodes
              stroke="#ffffff" // White border
              strokeWidth={1}
            />
            <text
              fill="#000000" // White text
              x="-5" // Offset text to the right of the node
              dy=".31em" // Vertical alignment
              fontSize="20" // Larger text for readability
            >
              {nodeDatum.name}
            </text>
          </g>
        )}
      />
    </div>
  </div>
)}
    </div>
  );
}

export default App;
