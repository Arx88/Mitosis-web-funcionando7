import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { AppContextProvider } from '../../context/AppContext'
import ChatInterface from '../ChatInterface'

const MockWrapper = ({ children }: { children: React.ReactNode }) => (
  <AppContextProvider>
    {children}
  </AppContextProvider>
)

describe('ChatInterface Component', () => {
  it('renders chat input field', () => {
    render(
      <MockWrapper>
        <ChatInterface />
      </MockWrapper>
    )
    
    const input = screen.getByPlaceholderText(/convierte tus ideas en realidad/i)
    expect(input).toBeInTheDocument()
  })

  it('allows typing in input field', async () => {
    render(
      <MockWrapper>
        <ChatInterface />
      </MockWrapper>
    )
    
    const input = screen.getByPlaceholderText(/convierte tus ideas en realidad/i)
    fireEvent.change(input, { target: { value: 'Test message' } })
    
    expect(input).toHaveValue('Test message')
  })

  it('shows send button', () => {
    render(
      <MockWrapper>
        <ChatInterface />
      </MockWrapper>
    )
    
    const sendButton = screen.getByRole('button', { name: /enviar/i })
    expect(sendButton).toBeInTheDocument()
  })

  it('displays messages correctly', () => {
    render(
      <MockWrapper>
        <ChatInterface />
      </MockWrapper>
    )
    
    // Verificar que el contenedor de mensajes existe
    const messagesContainer = screen.getByTestId('messages-container')
    expect(messagesContainer).toBeInTheDocument()
  })
})