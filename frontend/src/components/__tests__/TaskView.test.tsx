import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { AppContextProvider } from '../context/AppContext'
import TaskView from '../TaskView'

const mockTask = {
  id: 'test-task-1',
  title: 'Test Task',
  description: 'A test task for testing',
  status: 'active',
  createdAt: new Date().toISOString(),
  messages: [],
  plan: {
    title: 'Test Plan',
    description: 'Test plan description',
    steps: [
      {
        id: 'step-1',
        title: 'Test Step 1',
        description: 'First test step',
        tool: 'shell_tool',
        status: 'pending'
      }
    ]
  }
}

const MockWrapper = ({ children }: { children: React.ReactNode }) => (
  <AppContextProvider>
    {children}
  </AppContextProvider>
)

describe('TaskView Component', () => {
  it('renders task header correctly', () => {
    render(
      <MockWrapper>
        <TaskView />
      </MockWrapper>
    )
    
    // Verificar que el componente se renderiza
    expect(screen.getByRole('main')).toBeInTheDocument()
  })

  it('shows chat interface', () => {
    render(
      <MockWrapper>
        <TaskView />
      </MockWrapper>
    )
    
    // Verificar que existe el elemento de chat
    const chatContainer = screen.getByTestId('chat-container')
    expect(chatContainer).toBeInTheDocument()
  })

  it('shows terminal interface', () => {
    render(
      <MockWrapper>
        <TaskView />
      </MockWrapper>
    )
    
    // Verificar que existe el terminal
    const terminalContainer = screen.getByTestId('terminal-container')
    expect(terminalContainer).toBeInTheDocument()
  })
})