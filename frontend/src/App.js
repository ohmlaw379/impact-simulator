import React from "react";
import "./App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Toaster } from "./components/ui/toaster";
import Simulator from "./components/Simulator";

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Simulator />} />
        </Routes>
      </BrowserRouter>
      <Toaster />
    </div>
  );
}

export default App;