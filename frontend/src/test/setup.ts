import '@testing-library/jest-dom'

// Mock socket.io-client para tests
vi.mock('socket.io-client', () => ({
  io: vi.fn(() => ({
    on: vi.fn(),
    emit: vi.fn(),
    disconnect: vi.fn(),
    connected: true,
  })),
}))

// Mock fetch globalmente
global.fetch = vi.fn()

// Setup para limpieza después de cada test
afterEach(() => {
  vi.clearAllMocks()
})