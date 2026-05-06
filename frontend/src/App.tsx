import { useState } from 'react'
import { Dashboard } from './pages/Dashboard'
import GalleryPage from './pages/GalleryPage'
import './App.css'

type Page = 'dashboard' | 'gallery'

function App() {
  const [page, setPage] = useState<Page>('dashboard')

  return (
    <div className="app">
      <nav className="app-nav">
        <span className="app-nav__brand">AeroSearch AI</span>
        <button
          className={`app-nav__btn${page === 'dashboard' ? ' app-nav__btn--active' : ''}`}
          onClick={() => setPage('dashboard')}
        >
          Dashboard
        </button>
        <button
          className={`app-nav__btn${page === 'gallery' ? ' app-nav__btn--active' : ''}`}
          onClick={() => setPage('gallery')}
        >
          Galería
        </button>
      </nav>
      <div className={`app-content${page === 'gallery' ? ' app-content--scrollable' : ''}`}>
        {page === 'dashboard' ? <Dashboard /> : <GalleryPage />}
      </div>
    </div>
  )
}

export default App
