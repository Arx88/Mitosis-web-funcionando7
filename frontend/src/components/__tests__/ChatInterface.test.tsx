import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { AppContextProvider } from '../../context/AppContext'
import ChatInterface from '../ChatInterface/ChatInterface'

const MockWrapper = ({ children }: { children: React.ReactNode }) => (
  <AppContextProvider>
    {children}
  </AppContextProvider>
)

describe('ChatInterface Component', () => {
  it('renders without crashing', () => {
    const { container } = render(
      <MockWrapper>
        <ChatInterface />
      </MockWrapper>
    )
    
    expect(container).toBeInTheDocument()
  })

  it('renders chat interface container', () => {
    const { container } = render(
      <MockWrapper>
        <ChatInterface />
      </MockWrapper>
    )
    
    // Verificar que el componente se renderiza correctamente
    expect(container.firstChild).toBeInTheDocument()
  })
})