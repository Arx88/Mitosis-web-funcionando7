import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { AppContextProvider } from '../../context/AppContext'
import TaskView from '../TaskView'

const MockWrapper = ({ children }: { children: React.ReactNode }) => (
  <AppContextProvider>
    {children}
  </AppContextProvider>
)

describe('TaskView Component', () => {
  it('renders task view main container', () => {
    render(
      <MockWrapper>
        <TaskView />
      </MockWrapper>
    )
    
    // Verificar que el componente se renderiza
    const taskViewContainer = screen.getByRole('main')
    expect(taskViewContainer).toBeInTheDocument()
  })

  it('renders without crashing', () => {
    const { container } = render(
      <MockWrapper>
        <TaskView />
      </MockWrapper>
    )
    
    expect(container).toBeInTheDocument()
  })
})