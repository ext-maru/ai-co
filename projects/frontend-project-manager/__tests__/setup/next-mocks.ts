// Mock implementation for Next.js server components

export class MockNextRequest {
  url: URL
  method: string
  headers: Headers
  private _body: string | undefined

  constructor(input: string | URL, init?: RequestInit) {
    this.url = new URL(input)
    this.method = init?.method || 'GET'
    this.headers = new Headers(init?.headers)
    this._body = init?.body as string
  }

  async json() {
    if (!this._body) return {}
    try {
      return JSON.parse(this._body)
    } catch {
      return {}
    }
  }

  async text() {
    return this._body || ''
  }

  clone() {
    return new MockNextRequest(this.url.toString(), {
      method: this.method,
      headers: this.headers,
      body: this._body,
    })
  }
}

export class MockNextResponse {
  static json(data: any, init?: ResponseInit) {
    const response = new Response(JSON.stringify(data), {
      ...init,
      headers: {
        'content-type': 'application/json',
        ...(init?.headers || {}),
      },
    })
    // Monkey-patch the json method
    ;(response as any).json = () => Promise.resolve(data)
    return response
  }

  static redirect(url: string, status = 302) {
    return new Response(null, {
      status,
      headers: {
        Location: url,
      },
    })
  }

  static rewrite(url: string) {
    return new Response(null, {
      headers: {
        'x-middleware-rewrite': url,
      },
    })
  }

  static next() {
    return new Response(null, {
      headers: {
        'x-middleware-next': '1',
      },
    })
  }
}
