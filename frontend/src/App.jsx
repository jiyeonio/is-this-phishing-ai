import { useEffect, useState } from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import AppShell from './components/AppShell'
import Splash from './components/Splash'
import Analyze from './pages/Analyze'
import Report from './pages/Report'
import Trends from './pages/Trends'
import Lookup from './pages/Lookup'
import Guide from './pages/Guide'

const SPLASH_DURATION_MS = 1300

function App() {
  const [showSplash, setShowSplash] = useState(true)

  useEffect(() => {
    const timer = setTimeout(() => setShowSplash(false), SPLASH_DURATION_MS)
    return () => clearTimeout(timer)
  }, [])

  if (showSplash) return <Splash />

  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppShell />}>
          <Route path="/" element={<Analyze />} />
          <Route path="/report" element={<Report />} />
          <Route path="/trends" element={<Trends />} />
          <Route path="/lookup" element={<Lookup />} />
          <Route path="/guide" element={<Guide />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App
