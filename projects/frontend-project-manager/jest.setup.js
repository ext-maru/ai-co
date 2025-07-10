// Learn more: https://github.com/testing-library/jest-dom
import '@testing-library/jest-dom'
import 'isomorphic-fetch'

const { TextEncoder, TextDecoder } = require('util')
global.TextEncoder = TextEncoder
global.TextDecoder = TextDecoder

// Set up environment
process.env.NODE_ENV = 'test'

// Mock for Next.js App Router
class MockNextRequest extends Request {
  constructor(input, init) {
    super(input, init)
  }
}

class MockNextResponse extends Response {
  static json(body, init) {
    const response = new Response(JSON.stringify(body), {
      ...init,
      headers: {
        'content-type': 'application/json',
        ...(init?.headers || {})
      }
    })
    // Override json method for testing
    response.json = () => Promise.resolve(body)
    return response
  }
}

jest.mock('next/server', () => ({
  NextRequest: MockNextRequest,
  NextResponse: MockNextResponse
}))

// Mock next/navigation
jest.mock('next/navigation', () => ({
  useRouter() {
    return {
      push: jest.fn(),
      replace: jest.fn(),
      prefetch: jest.fn(),
      back: jest.fn(),
    }
  },
  useSearchParams() {
    return new URLSearchParams()
  },
  usePathname() {
    return ''
  },
}))

// Reset mocks before each test
beforeEach(() => {
  jest.clearAllMocks()
})