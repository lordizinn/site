import React from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider } from "@/context/AuthContext";
import { Toaster } from "@/components/ui/sonner";
import LandingPage from "@/pages/LandingPage";
import SubscribePage from "@/pages/SubscribePage";
import SuccessPage from "@/pages/SuccessPage";
import LoginPage from "@/pages/LoginPage";
import Dashboard from "@/pages/Dashboard";

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <AuthProvider>
          <Routes>
            <Route path="/" element={<LandingPage />} />
            <Route path="/subscribe" element={<SubscribePage />} />
            <Route path="/subscription/success" element={<SuccessPage />} />
            <Route path="/subscription/failure" element={<Navigate to="/subscribe" />} />
            <Route path="/subscription/pending" element={<Navigate to="/subscribe" />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/dashboard" element={<Dashboard />} />
          </Routes>
          <Toaster position="top-right" />
        </AuthProvider>
      </BrowserRouter>
    </div>
  );
}

export default App;
