import { BrowserRouter as Router, Routes, Route } from "react-router-dom"
import Dashboard from "./pages/Dashboard"
import ServerDataCenterPage from "./pages/ServerDataPage"

export default function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/servers" element={<ServerDataCenterPage />} />
      </Routes>
    </Router>
  )
}
