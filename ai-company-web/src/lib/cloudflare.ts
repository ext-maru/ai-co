/**
 * Cloudflare integration utilities
 */

interface CloudflareEnv {
  CACHE_KV: KVNamespace;
  SESSION_KV: KVNamespace;
  ASSETS_BUCKET: R2Bucket;
  ANALYTICS: AnalyticsEngineDataset;
  TASK_QUEUE: Queue;
  WEBSOCKET_DO: DurableObjectNamespace;
}

export class CloudflareCache {
  private kv: KVNamespace;
  
  constructor(kv: KVNamespace) {
    this.kv = kv;
  }

  async get<T>(key: string): Promise<T | null> {
    try {
      const value = await this.kv.get(key, 'json');
      return value as T;
    } catch (error) {
      console.error('Cloudflare KV get error:', error);
      return null;
    }
  }

  async set<T>(key: string, value: T, options?: { ttl?: number }): Promise<void> {
    try {
      const putOptions: any = {};
      if (options?.ttl) {
        putOptions.expirationTtl = options.ttl;
      }
      
      await this.kv.put(key, JSON.stringify(value), putOptions);
    } catch (error) {
      console.error('Cloudflare KV set error:', error);
    }
  }

  async delete(key: string): Promise<void> {
    try {
      await this.kv.delete(key);
    } catch (error) {
      console.error('Cloudflare KV delete error:', error);
    }
  }

  async list(prefix?: string): Promise<string[]> {
    try {
      const options: any = {};
      if (prefix) {
        options.prefix = prefix;
      }
      
      const result = await this.kv.list(options);
      return result.keys.map(key => key.name);
    } catch (error) {
      console.error('Cloudflare KV list error:', error);
      return [];
    }
  }
}

export class CloudflareAssets {
  private bucket: R2Bucket;
  
  constructor(bucket: R2Bucket) {
    this.bucket = bucket;
  }

  async upload(key: string, data: ArrayBuffer | Uint8Array | string, options?: {
    contentType?: string;
    metadata?: Record<string, string>;
  }): Promise<void> {
    try {
      const putOptions: R2PutOptions = {};
      
      if (options?.contentType) {
        putOptions.httpMetadata = {
          contentType: options.contentType
        };
      }
      
      if (options?.metadata) {
        putOptions.customMetadata = options.metadata;
      }
      
      await this.bucket.put(key, data, putOptions);
    } catch (error) {
      console.error('Cloudflare R2 upload error:', error);
      throw error;
    }
  }

  async download(key: string): Promise<ArrayBuffer | null> {
    try {
      const object = await this.bucket.get(key);
      if (!object) return null;
      
      return await object.arrayBuffer();
    } catch (error) {
      console.error('Cloudflare R2 download error:', error);
      return null;
    }
  }

  async delete(key: string): Promise<void> {
    try {
      await this.bucket.delete(key);
    } catch (error) {
      console.error('Cloudflare R2 delete error:', error);
    }
  }

  async list(prefix?: string): Promise<string[]> {
    try {
      const options: R2ListOptions = {};
      if (prefix) {
        options.prefix = prefix;
      }
      
      const result = await this.bucket.list(options);
      return result.objects.map(obj => obj.key);
    } catch (error) {
      console.error('Cloudflare R2 list error:', error);
      return [];
    }
  }
}

export class CloudflareAnalytics {
  private analytics: AnalyticsEngineDataset;
  
  constructor(analytics: AnalyticsEngineDataset) {
    this.analytics = analytics;
  }

  async writeDataPoint(data: {
    timestamp?: Date;
    indexes?: string[];
    doubles?: number[];
    blobs?: string[];
  }): Promise<void> {
    try {
      await this.analytics.writeDataPoint({
        timestamp: data.timestamp || new Date(),
        indexes: data.indexes || [],
        doubles: data.doubles || [],
        blobs: data.blobs || []
      });
    } catch (error) {
      console.error('Cloudflare Analytics write error:', error);
    }
  }

  async trackPageView(page: string, userAgent?: string, country?: string): Promise<void> {
    await this.writeDataPoint({
      indexes: ['page_view', page],
      blobs: [userAgent || '', country || ''],
      doubles: [1]
    });
  }

  async trackApiCall(endpoint: string, method: string, statusCode: number, responseTime: number): Promise<void> {
    await this.writeDataPoint({
      indexes: ['api_call', endpoint, method, statusCode.toString()],
      doubles: [1, responseTime]
    });
  }

  async trackError(error: string, page: string, userAgent?: string): Promise<void> {
    await this.writeDataPoint({
      indexes: ['error', page],
      blobs: [error, userAgent || ''],
      doubles: [1]
    });
  }

  async trackPerformance(metric: string, value: number, page: string): Promise<void> {
    await this.writeDataPoint({
      indexes: ['performance', metric, page],
      doubles: [value]
    });
  }
}

export class CloudflareQueue {
  private queue: Queue;
  
  constructor(queue: Queue) {
    this.queue = queue;
  }

  async send(message: any, options?: {
    contentType?: string;
    delaySeconds?: number;
  }): Promise<void> {
    try {
      const sendOptions: any = {};
      
      if (options?.contentType) {
        sendOptions.contentType = options.contentType;
      }
      
      if (options?.delaySeconds) {
        sendOptions.delaySeconds = options.delaySeconds;
      }
      
      await this.queue.send(message, sendOptions);
    } catch (error) {
      console.error('Cloudflare Queue send error:', error);
      throw error;
    }
  }

  async sendBatch(messages: any[]): Promise<void> {
    try {
      await this.queue.sendBatch(messages.map(msg => ({ body: msg })));
    } catch (error) {
      console.error('Cloudflare Queue sendBatch error:', error);
      throw error;
    }
  }
}

// Edge-side request handling
export class EdgeRequestHandler {
  static async handleRequest(request: Request, env: CloudflareEnv, ctx: ExecutionContext): Promise<Response> {
    const url = new URL(request.url);
    const cache = new CloudflareCache(env.CACHE_KV);
    const analytics = new CloudflareAnalytics(env.ANALYTICS);
    
    // Track request
    const startTime = Date.now();
    
    try {
      // Check cache first for GET requests
      if (request.method === 'GET') {
        const cacheKey = `page:${url.pathname}`;
        const cached = await cache.get<string>(cacheKey);
        
        if (cached) {
          await analytics.trackPageView(url.pathname, request.headers.get('user-agent') || undefined);
          return new Response(cached, {
            headers: {
              'Content-Type': 'text/html',
              'Cache-Control': 'public, max-age=3600',
              'X-Cache': 'HIT'
            }
          });
        }
      }
      
      // Handle API requests
      if (url.pathname.startsWith('/api/')) {
        return await this.handleApiRequest(request, env, analytics);
      }
      
      // Handle static assets
      if (this.isStaticAsset(url.pathname)) {
        return await this.handleStaticAsset(request, env);
      }
      
      // Handle page requests
      const response = await this.handlePageRequest(request, env, cache);
      
      // Track analytics
      const responseTime = Date.now() - startTime;
      await analytics.trackPageView(url.pathname, request.headers.get('user-agent') || undefined);
      await analytics.trackPerformance('response_time', responseTime, url.pathname);
      
      return response;
      
    } catch (error) {
      // Track error
      await analytics.trackError(error.message, url.pathname, request.headers.get('user-agent') || undefined);
      
      return new Response('Internal Server Error', {
        status: 500,
        headers: {
          'Content-Type': 'text/plain',
          'X-Error': 'edge-function-error'
        }
      });
    }
  }

  private static async handleApiRequest(request: Request, env: CloudflareEnv, analytics: CloudflareAnalytics): Promise<Response> {
    const url = new URL(request.url);
    const startTime = Date.now();
    
    // Proxy to backend API
    const backendUrl = `${env.API_BASE_URL}${url.pathname}${url.search}`;
    
    const response = await fetch(backendUrl, {
      method: request.method,
      headers: request.headers,
      body: request.method !== 'GET' ? request.body : undefined
    });
    
    // Track API call
    const responseTime = Date.now() - startTime;
    await analytics.trackApiCall(url.pathname, request.method, response.status, responseTime);
    
    return response;
  }

  private static async handleStaticAsset(request: Request, env: CloudflareEnv): Promise<Response> {
    const url = new URL(request.url);
    const assets = new CloudflareAssets(env.ASSETS_BUCKET);
    
    // Try to get from R2 bucket
    const asset = await assets.download(url.pathname.slice(1)); // Remove leading slash
    
    if (asset) {
      const contentType = this.getContentType(url.pathname);
      
      return new Response(asset, {
        headers: {
          'Content-Type': contentType,
          'Cache-Control': 'public, max-age=31536000, immutable',
          'X-Source': 'r2-bucket'
        }
      });
    }
    
    return new Response('Not Found', { status: 404 });
  }

  private static async handlePageRequest(request: Request, env: CloudflareEnv, cache: CloudflareCache): Promise<Response> {
    const url = new URL(request.url);
    
    // Generate or fetch page content
    // This would typically render your React app
    const pageContent = await this.renderPage(url.pathname, request, env);
    
    // Cache the page if it's cacheable
    if (this.isCacheable(url.pathname)) {
      const cacheKey = `page:${url.pathname}`;
      await cache.set(cacheKey, pageContent, { ttl: 3600 }); // 1 hour TTL
    }
    
    return new Response(pageContent, {
      headers: {
        'Content-Type': 'text/html',
        'Cache-Control': this.getCacheControl(url.pathname),
        'X-Cache': 'MISS'
      }
    });
  }

  private static async renderPage(pathname: string, request: Request, env: CloudflareEnv): Promise<string> {
    // This is a simplified example - in reality, you'd use a proper SSR setup
    return `
      <!DOCTYPE html>
      <html lang="en">
        <head>
          <meta charset="UTF-8">
          <meta name="viewport" content="width=device-width, initial-scale=1.0">
          <title>AI Company Web</title>
          <link rel="stylesheet" href="/styles/main.css">
        </head>
        <body>
          <div id="root">
            <h1>AI Company Web - ${pathname}</h1>
            <p>Rendered at the edge with Cloudflare Workers</p>
          </div>
          <script src="/scripts/main.js"></script>
        </body>
      </html>
    `;
  }

  private static isStaticAsset(pathname: string): boolean {
    const staticExtensions = ['.js', '.css', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.woff', '.woff2', '.ttf'];
    return staticExtensions.some(ext => pathname.endsWith(ext));
  }

  private static isCacheable(pathname: string): boolean {
    // Don't cache dynamic pages or API routes
    return !pathname.startsWith('/api/') && !pathname.includes('/dashboard/');
  }

  private static getCacheControl(pathname: string): string {
    if (pathname.startsWith('/api/')) {
      return 'private, no-cache, no-store, must-revalidate';
    }
    
    if (this.isStaticAsset(pathname)) {
      return 'public, max-age=31536000, immutable';
    }
    
    return 'public, max-age=3600';
  }

  private static getContentType(pathname: string): string {
    const extension = pathname.split('.').pop()?.toLowerCase();
    
    const contentTypes: Record<string, string> = {
      'html': 'text/html',
      'css': 'text/css',
      'js': 'application/javascript',
      'json': 'application/json',
      'png': 'image/png',
      'jpg': 'image/jpeg',
      'jpeg': 'image/jpeg',
      'gif': 'image/gif',
      'svg': 'image/svg+xml',
      'ico': 'image/x-icon',
      'woff': 'font/woff',
      'woff2': 'font/woff2',
      'ttf': 'font/ttf'
    };
    
    return contentTypes[extension || ''] || 'application/octet-stream';
  }
}

// Cloudflare integration for client-side
export class CloudflareBrowser {
  static async preloadCriticalResources(): Promise<void> {
    if (typeof window === 'undefined') return;
    
    // Use Cloudflare's edge to preload critical resources
    const criticalResources = [
      '/api/v1/sages/status',
      '/api/v1/elder-council/status',
      '/styles/critical.css',
      '/scripts/main.js'
    ];
    
    criticalResources.forEach(resource => {
      const link = document.createElement('link');
      link.rel = 'preload';
      link.href = resource;
      
      if (resource.endsWith('.css')) {
        link.as = 'style';
      } else if (resource.endsWith('.js')) {
        link.as = 'script';
      } else {
        link.as = 'fetch';
        link.crossOrigin = 'anonymous';
      }
      
      document.head.appendChild(link);
    });
  }

  static async measureNetworkPerformance(): Promise<{
    latency: number;
    bandwidth: number;
    region: string;
  }> {
    const startTime = performance.now();
    
    try {
      // Use Cloudflare's speed test endpoint
      const response = await fetch('/cdn-cgi/trace', {
        cache: 'no-cache'
      });
      
      const endTime = performance.now();
      const latency = endTime - startTime;
      
      const text = await response.text();
      const lines = text.split('\n');
      const data: Record<string, string> = {};
      
      lines.forEach(line => {
        const [key, value] = line.split('=');
        if (key && value) {
          data[key] = value;
        }
      });
      
      // Estimate bandwidth (very rough approximation)
      const dataSize = text.length;
      const bandwidth = (dataSize * 8) / (latency / 1000); // bits per second
      
      return {
        latency,
        bandwidth,
        region: data.colo || 'unknown'
      };
      
    } catch (error) {
      console.error('Network performance measurement failed:', error);
      return {
        latency: 0,
        bandwidth: 0,
        region: 'unknown'
      };
    }
  }
}

// Export the main handler for Cloudflare Workers
export default {
  async fetch(request: Request, env: CloudflareEnv, ctx: ExecutionContext): Promise<Response> {
    return EdgeRequestHandler.handleRequest(request, env, ctx);
  }
};