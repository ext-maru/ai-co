// Mock NextResponse for testing
export const mockJson = jest.fn()
export const mockText = jest.fn()

// Mock the Response object
class MockResponse {
  constructor(public body: any, public init?: ResponseInit) {}
  
  json() {
    return Promise.resolve(typeof this.body === 'string' ? JSON.parse(this.body) : this.body)
  }
  
  text() {
    return Promise.resolve(typeof this.body === 'string' ? this.body : JSON.stringify(this.body))
  }
  
  get status() {
    return this.init?.status || 200
  }
}

class MockNextResponse extends MockResponse {
  static json(body: any, init?: ResponseInit) {
    mockJson(body, init)
    return new MockNextResponse(body, init)
  }
}

// Mock NextRequest for testing
export class MockNextRequest extends Request {
  constructor(url: string, init?: RequestInit) {
    super(url, {
      ...init,
      headers: new Headers(init?.headers)
    })
  }

  async json() {
    try {
      const text = await this.text()
      return text ? JSON.parse(text) : {}
    } catch {
      return {}
    }
  }
}

// Export as next/server module
export const NextResponse = MockNextResponse
export const NextRequest = MockNextRequest