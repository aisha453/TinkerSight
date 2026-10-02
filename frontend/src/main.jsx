import React from 'react'
import { createRoot } from 'react-dom/client'
import './styles.css'

const demoSteps = [
  'Put the clothes inside.',
  'Press the round button on the right.',
  'Press the temperature button 3 times.',
]

function App() {
  const [step, setStep] = React.useState(0)
  const [started, setStarted] = React.useState(false)

  return (
    <main className="shell">
      <header className="topbar">
        <div className="brand"><span className="mark">T</span> TinkerSight</div>
        <span className="local">● Local AI prototype</span>
      </header>

      <section className="hero">
        <p className="eyebrow">EVERYDAY TECHNICAL HELP</p>
        <h1>Show it. Tell us what you want.<br /><em>We'll guide you.</em></h1>
        <p className="subtitle">Simple instructions for appliances and everyday equipment — grounded in the right manual, not technical jargon.</p>

        {!started ? (
          <div className="capture">
            <div className="capture-icon">＋</div>
            <h2>Show TinkerSight your device</h2>
            <p>Upload a photo of the appliance or control panel.</p>
            <button onClick={() => setStarted(true)}>Upload a photo</button>
            <small>Demo mode — no image is uploaded yet</small>
          </div>
        ) : (
          <div className="guide-card">
            <div className="device-row">
              <div className="device-photo">WASHING<br />MACHINE</div>
              <div><span className="pill">MANUAL FOUND</span><h3>Ready to guide you</h3><p>We've identified the control panel for this demo.</p></div>
            </div>
            <div className="step-label">STEP {step + 1} OF {demoSteps.length}</div>
            <div className="step">{demoSteps[step]}</div>
            <button onClick={() => step < demoSteps.length - 1 ? setStep(step + 1) : setStarted(false)}>
              {step < demoSteps.length - 1 ? 'Done — next step' : 'Finish'}
            </button>
            <p className="question">{step < demoSteps.length - 1 ? 'Follow just this step, then continue.' : 'That’s it. No manual decoding required.'}</p>
          </div>
        )}
      </section>

      <section className="principles">
        <div><b>01</b><span>SEE</span><p>Understand the device from the user's photo.</p></div>
        <div><b>02</b><span>GROUND</span><p>Use the manufacturer's documentation.</p></div>
        <div><b>03</b><span>SIMPLIFY</span><p>Turn technical language into ordinary words.</p></div>
        <div><b>04</b><span>GUIDE</span><p>Give one safe action at a time.</p></div>
      </section>
    </main>
  )
}

createRoot(document.getElementById('root')).render(<App />)
