import React from 'react'
import { createRoot } from 'react-dom/client'
import './styles.css'

function App() {
  const [image, setImage] = React.useState(null)
  const [file, setFile] = React.useState(null)
  const [started, setStarted] = React.useState(false)
  const [goal, setGoal] = React.useState('')
  const [result, setResult] = React.useState(null)
  const [loading, setLoading] = React.useState(false)
  const [error, setError] = React.useState('')

  function handleImage(event) {
    const selected = event.target.files?.[0]
    if (!selected) return
    setFile(selected)
    setImage(URL.createObjectURL(selected))
    setStarted(true)
    setResult(null)
    setError('')
  }

  async function resizeImageForAI(sourceFile, maxDimension, quality) {
    if (!sourceFile.type.startsWith('image/')) return sourceFile

    const bitmap = await createImageBitmap(sourceFile)
    const scale = Math.min(1, maxDimension / Math.max(bitmap.width, bitmap.height))
    const width = Math.max(1, Math.round(bitmap.width * scale))
    const height = Math.max(1, Math.round(bitmap.height * scale))

    if (scale === 1 && sourceFile.type === 'image/jpeg') return sourceFile

    const canvas = document.createElement('canvas')
    canvas.width = width
    canvas.height = height
    canvas.getContext('2d').drawImage(bitmap, 0, 0, width, height)

    const blob = await new Promise((resolve) =>
      canvas.toBlob(resolve, 'image/jpeg', quality)
    )

    return blob || sourceFile
  }

  async function analyze() {
    if (!file || !goal.trim()) return

    setLoading(true)
    setError('')
    setResult(null)

    try {
      // Keep the original photo for the UI, but send a smaller copy to the
      // local vision model so image inference has less data to process.
      const optimizedImage = await resizeImageForAI(file, 1280, 0.82)

      const form = new FormData()
      form.append('image', optimizedImage, 'tinkersight-input.jpg')
      form.append('goal', goal)

      const response = await fetch('http://localhost:8000/api/guide', {
        method: 'POST',
        body: form,
      })

      if (!response.ok) throw new Error('TinkerSight could not reach the local AI service.')

      setResult(await response.json())
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  function reset() {
    setImage(null)
    setFile(null)
    setStarted(false)
    setGoal('')
    setResult(null)
    setError('')
  }

  return (
    <main className="shell">
      <header className="topbar">
        <div className="brand"><span className="mark">T</span> TinkerSight</div>
        <span className="local">● Local AI</span>
      </header>

      <section className="hero">
        <p className="eyebrow">EVERYDAY TECHNICAL HELP</p>
        <h1>Show it. Tell us what you want.<br /><em>We'll guide you.</em></h1>
        <p className="subtitle">
          Simple guidance for devices, appliances, and everyday equipment — grounded in manufacturer documentation when verified.
        </p>

        {!started ? (
          <div className="capture">
            <div className="capture-icon">＋</div>
            <h2>Show TinkerSight your device</h2>
            <p>Upload a photo of the device, appliance, control panel, or setup.</p>
            <label className="upload-button">
              Upload a photo
              <input type="file" accept="image/*" onChange={handleImage} />
            </label>
            <small>Your photo is sent to your local TinkerSight service for analysis.</small>
          </div>
        ) : (
          <div className="guide-card">
            <div className="device-row">
              <img className="device-photo image-preview" src={image} alt="Uploaded appliance" />
              <div>
                <span className="pill">{result ? 'AI ANALYSIS READY' : 'PHOTO RECEIVED'}</span>
                <h3>{result?.appliance || 'Let’s figure it out.'}</h3>
                <p>{result?.observation || 'Tell TinkerSight what you want to do.'}</p>
                {(result?.brand || result?.model) && (
                  <small className="model-line">
                    {result.brand && <>Brand: {result.brand}</>}
                    {result.brand && result.model && ' · '}
                    {result.model && <>Model: {result.model}</>}
                  </small>
                )}
              </div>
            </div>

            {!result ? (
              <div className="goal-box">
                <div className="step-label">WHAT DO YOU WANT TO DO?</div>
                <input
                  value={goal}
                  onChange={(event) => setGoal(event.target.value)}
                  placeholder="e.g. How do I connect this to Wi-Fi?"
                  onKeyDown={(event) => event.key === 'Enter' && analyze()}
                />
                <button disabled={!goal.trim() || loading} onClick={analyze}>
                  {loading ? 'Looking at it…' : 'Start guide'}
                </button>
                {error && <p className="error">{error}</p>}
              </div>
            ) : (
              <div className="result">
                <div className="meta-row">
                  <span className="pill">{result.confidence} confidence</span>
                  <span className={result.safety === 'normal' ? 'safe' : 'warn'}>{result.safety}</span>
                </div>
                <div className="step-label">NEXT STEP</div>
                <div className="step">{result.step}</div>
                {result.question && <p className="question"><strong>One thing I need to know:</strong> {result.question}</p>}
                <p className="manual">{result.manual_note}</p>
                {result.source_url && (
                  <div className="source">
                    <span>GROUNDED IN</span>
                    <a href={result.source_url} target="_blank" rel="noreferrer">
                      {result.source_title || 'Official manufacturer documentation'}
                    </a>
                    {result.source_note && <small>{result.source_note}</small>}
                  </div>
                )}
              </div>
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
