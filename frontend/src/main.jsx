import React from 'react'
import { createRoot } from 'react-dom/client'
import './styles.css'

const demoSteps = [
  'Tell me what you want the appliance to do.',
  'I’ll check the visible controls and the official guide.',
  'Then I’ll give you one simple action at a time.',
]

function App() {
  const [image, setImage] = React.useState(null)
  const [started, setStarted] = React.useState(false)
  const [step, setStep] = React.useState(0)
  const [goal, setGoal] = React.useState('')

  function handleImage(event) {
    const file = event.target.files?.[0]
    if (!file) return
    setImage(URL.createObjectURL(file))
    setStarted(true)
    setStep(0)
  }

  function reset() {
    setImage(null)
    setStarted(false)
    setStep(0)
    setGoal('')
  }

  return (
    <main className="shell">
      <header className="topbar">
        <div className="brand"><span className="mark">T</span> TinkerSight</div>
        <span className="local">● Local AI prototype</span>
      </header>

      <section className="hero">
        <p className="eyebrow">EVERYDAY TECHNICAL HELP</p>
        <h1>Show it. Tell us what you want.<br /><em>We'll guide you.</em></h1>
        <p className="subtitle">
          Simple instructions for appliances and everyday equipment — grounded in the right manual, not technical jargon.
        </p>

        {!started ? (
          <div className="capture">
            <div className="capture-icon">＋</div>
            <h2>Show TinkerSight your device</h2>
            <p>Upload a photo of the appliance or control panel.</p>

            <label className="upload-button">
              Upload a photo
              <input type="file" accept="image/*" onChange={handleImage} />
            </label>

            <small>Your photo stays in this prototype until we connect the local AI.</small>
          </div>
        ) : (
          <div className="guide-card">
            <div className="device-row">
              {image ? (
                <img className="device-photo image-preview" src={image} alt="Uploaded appliance" />
              ) : (
                <div className="device-photo">DEVICE<br />PHOTO</div>
              )}

              <div>
                <span className="pill">PHOTO RECEIVED</span>
                <h3>Let's figure it out.</h3>
                <p>TinkerSight will inspect the controls and use the correct manual.</p>
              </div>
            </div>

            {step === 0 ? (
              <div className="goal-box">
                <div className="step-label">WHAT DO YOU WANT TO DO?</div>
                <input
                  value={goal}
                  onChange={(event) => setGoal(event.target.value)}
                  placeholder="e.g. Set the washing machine to 60°C"
                />
                <button disabled={!goal.trim()} onClick={() => setStep(1)}>
                  Start guide
                </button>
              </div>
            ) : (
              <>
                <div className="step-label">STEP {step} OF {demoSteps.length - 1}</div>
                <div className="step">{demoSteps[step]}</div>
                <button onClick={() => step < demoSteps.length - 1 ? setStep(step + 1) : reset()}>
                  {step < demoSteps.length - 1 ? 'Done — next step' : 'Start another device'}
                </button>
                <p className="question">
                  {step < demoSteps.length - 1 ? 'No technical terms. Just the next action.' : 'Ready for another task.'}
                </p>
              </>
            )}

            <button className="secondary-button" onClick={reset}>Choose another photo</button>
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
