import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import './App.css';

import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import AverageLengthOfStay from './pages/AverageLengthOfStay';
import CostsPerPatient from './pages/CostsPerPatient';
import HospitalExpenses from './pages/HospitalExpenses';
import MortalityRate from './pages/MortalityRate';
import PatientOperations from './pages/PatientOperations';
import ExpenseEntry from './pages/ExpenseEntry';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Login />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/average-length-of-stay" element={<AverageLengthOfStay />} />
        <Route path="/costs-per-patient" element={<CostsPerPatient />} />
        <Route path="/hospital-expenses" element={<HospitalExpenses />} />
        <Route path="/mortality-rate" element={<MortalityRate />} />
        <Route path="/patient-operations" element={<PatientOperations />} />
        <Route path="/expense-entry" element={<ExpenseEntry />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
