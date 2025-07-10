/**
 * Performance monitoring and Core Web Vitals optimization
 */

// Core Web Vitals types
interface WebVital {
  name: string;
  value: number;
  rating: 'good' | 'needs-improvement' | 'poor';
  delta: number;
  id: string;
}

interface PerformanceMetrics {
  fcp: number;  // First Contentful Paint
  lcp: number;  // Largest Contentful Paint
  fid: number;  // First Input Delay
  cls: number;  // Cumulative Layout Shift
  ttfb: number; // Time to First Byte
}

class PerformanceMonitor {
  private metrics: Partial<PerformanceMetrics> = {};
  private observers: PerformanceObserver[] = [];

  constructor() {
    this.initializeObservers();
  }

  private initializeObservers() {
    // Only run in browser
    if (typeof window === 'undefined') return;

    try {
      // Largest Contentful Paint (LCP)
      this.observeLCP();
      
      // First Input Delay (FID)
      this.observeFID();
      
      // Cumulative Layout Shift (CLS)
      this.observeCLS();
      
      // First Contentful Paint (FCP)
      this.observeFCP();
      
      // Time to First Byte (TTFB)
      this.observeTTFB();

    } catch (error) {
      console.warn('Performance observers not supported:', error);
    }
  }

  private observeLCP() {
    if (!('PerformanceObserver' in window)) return;

    const observer = new PerformanceObserver((list) => {
      const entries = list.getEntries();
      const lastEntry = entries[entries.length - 1] as any;
      
      if (lastEntry) {
        this.metrics.lcp = lastEntry.startTime;
        this.reportWebVital({
          name: 'LCP',
          value: lastEntry.startTime,
          rating: this.getRating('LCP', lastEntry.startTime),
          delta: lastEntry.startTime - (this.metrics.lcp || 0),
          id: this.generateId()
        });
      }
    });

    observer.observe({ entryTypes: ['largest-contentful-paint'] });
    this.observers.push(observer);
  }

  private observeFID() {
    if (!('PerformanceObserver' in window)) return;

    const observer = new PerformanceObserver((list) => {
      const entries = list.getEntries();
      
      entries.forEach((entry: any) => {
        if (entry.name === 'first-input') {
          const fid = entry.processingStart - entry.startTime;
          this.metrics.fid = fid;
          
          this.reportWebVital({
            name: 'FID',
            value: fid,
            rating: this.getRating('FID', fid),
            delta: fid - (this.metrics.fid || 0),
            id: this.generateId()
          });
        }
      });
    });

    observer.observe({ entryTypes: ['first-input'] });
    this.observers.push(observer);
  }

  private observeCLS() {
    if (!('PerformanceObserver' in window)) return;

    let clsValue = 0;
    let sessionValue = 0;
    let sessionEntries: any[] = [];

    const observer = new PerformanceObserver((list) => {
      const entries = list.getEntries();
      
      entries.forEach((entry: any) => {
        if (!entry.hadRecentInput) {
          const firstSessionEntry = sessionEntries[0];
          const lastSessionEntry = sessionEntries[sessionEntries.length - 1];

          if (sessionValue && 
              entry.startTime - lastSessionEntry.startTime < 1000 &&
              entry.startTime - firstSessionEntry.startTime < 5000) {
            sessionValue += entry.value;
            sessionEntries.push(entry);
          } else {
            sessionValue = entry.value;
            sessionEntries = [entry];
          }

          if (sessionValue > clsValue) {
            clsValue = sessionValue;
            this.metrics.cls = clsValue;
            
            this.reportWebVital({
              name: 'CLS',
              value: clsValue,
              rating: this.getRating('CLS', clsValue),
              delta: clsValue - (this.metrics.cls || 0),
              id: this.generateId()
            });
          }
        }
      });
    });

    observer.observe({ entryTypes: ['layout-shift'] });
    this.observers.push(observer);
  }

  private observeFCP() {
    if (!('PerformanceObserver' in window)) return;

    const observer = new PerformanceObserver((list) => {
      const entries = list.getEntries();
      
      entries.forEach((entry: any) => {
        if (entry.name === 'first-contentful-paint') {
          this.metrics.fcp = entry.startTime;
          
          this.reportWebVital({
            name: 'FCP',
            value: entry.startTime,
            rating: this.getRating('FCP', entry.startTime),
            delta: entry.startTime - (this.metrics.fcp || 0),
            id: this.generateId()
          });
        }
      });
    });

    observer.observe({ entryTypes: ['paint'] });
    this.observers.push(observer);
  }

  private observeTTFB() {
    if (!('PerformanceObserver' in window)) return;

    const observer = new PerformanceObserver((list) => {
      const entries = list.getEntries();
      
      entries.forEach((entry: any) => {
        if (entry.entryType === 'navigation') {
          const ttfb = entry.responseStart - entry.requestStart;
          this.metrics.ttfb = ttfb;
          
          this.reportWebVital({
            name: 'TTFB',
            value: ttfb,
            rating: this.getRating('TTFB', ttfb),
            delta: ttfb - (this.metrics.ttfb || 0),
            id: this.generateId()
          });
        }
      });
    });

    observer.observe({ entryTypes: ['navigation'] });
    this.observers.push(observer);
  }

  private getRating(metric: string, value: number): 'good' | 'needs-improvement' | 'poor' {
    const thresholds = {
      FCP: { good: 1800, poor: 3000 },
      LCP: { good: 2500, poor: 4000 },
      FID: { good: 100, poor: 300 },
      CLS: { good: 0.1, poor: 0.25 },
      TTFB: { good: 800, poor: 1800 }
    };

    const threshold = thresholds[metric as keyof typeof thresholds];
    if (!threshold) return 'good';

    if (value <= threshold.good) return 'good';
    if (value <= threshold.poor) return 'needs-improvement';
    return 'poor';
  }

  private reportWebVital(vital: WebVital) {
    // Send to analytics
    this.sendToAnalytics(vital);
    
    // Log to console in development
    if (process.env.NODE_ENV === 'development') {
      console.log(`[Performance] ${vital.name}: ${vital.value.toFixed(2)}ms (${vital.rating})`);
    }

    // Send alert if performance is poor
    if (vital.rating === 'poor') {
      this.sendPerformanceAlert(vital);
    }
  }

  private sendToAnalytics(vital: WebVital) {
    // Implementation would send to your analytics service
    // e.g., Google Analytics, Mixpanel, etc.
    if (typeof window !== 'undefined' && (window as any).gtag) {
      (window as any).gtag('event', vital.name, {
        event_category: 'Web Vitals',
        value: Math.round(vital.value),
        custom_parameter_1: vital.rating,
        non_interaction: true,
      });
    }
  }

  private sendPerformanceAlert(vital: WebVital) {
    // Send alert for poor performance
    fetch('/api/v1/monitoring/performance-alert', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        metric: vital.name,
        value: vital.value,
        rating: vital.rating,
        url: window.location.href,
        userAgent: navigator.userAgent,
        timestamp: Date.now()
      })
    }).catch(error => {
      console.warn('Failed to send performance alert:', error);
    });
  }

  private generateId(): string {
    return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }

  public getMetrics(): Partial<PerformanceMetrics> {
    return { ...this.metrics };
  }

  public destroy() {
    this.observers.forEach(observer => observer.disconnect());
    this.observers = [];
  }
}

// Resource optimization utilities
export class ResourceOptimizer {
  static preloadCriticalResources() {
    if (typeof document === 'undefined') return;

    // Preload critical fonts
    const fonts = [
      '/fonts/inter-var.woff2',
      '/fonts/roboto-mono.woff2'
    ];

    fonts.forEach(font => {
      const link = document.createElement('link');
      link.rel = 'preload';
      link.as = 'font';
      link.type = 'font/woff2';
      link.crossOrigin = 'anonymous';
      link.href = font;
      document.head.appendChild(link);
    });

    // Preload critical API endpoints
    const criticalEndpoints = [
      '/api/v1/sages/status',
      '/api/v1/elder-council/status'
    ];

    criticalEndpoints.forEach(endpoint => {
      const link = document.createElement('link');
      link.rel = 'preload';
      link.as = 'fetch';
      link.crossOrigin = 'anonymous';
      link.href = endpoint;
      document.head.appendChild(link);
    });
  }

  static optimizeImages() {
    if (typeof document === 'undefined') return;

    // Implement lazy loading for images
    const images = document.querySelectorAll('img[data-src]');
    
    if ('IntersectionObserver' in window) {
      const imageObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            const img = entry.target as HTMLImageElement;
            img.src = img.dataset.src!;
            img.classList.remove('lazy');
            imageObserver.unobserve(img);
          }
        });
      });

      images.forEach(img => imageObserver.observe(img));
    } else {
      // Fallback for browsers without IntersectionObserver
      images.forEach((img: any) => {
        img.src = img.dataset.src;
      });
    }
  }

  static implementCriticalCSS() {
    if (typeof document === 'undefined') return;

    // Load non-critical CSS asynchronously
    const nonCriticalCSS = document.querySelectorAll('link[rel="stylesheet"][data-priority="low"]');
    
    nonCriticalCSS.forEach(link => {
      const newLink = document.createElement('link');
      newLink.rel = 'stylesheet';
      newLink.href = (link as HTMLLinkElement).href;
      newLink.media = 'print';
      newLink.onload = function() {
        newLink.media = 'all';
      };
      
      document.head.appendChild(newLink);
      link.remove();
    });
  }
}

// Bundle analyzer for development
export class BundleAnalyzer {
  static analyzeBundles() {
    if (process.env.NODE_ENV !== 'development') return;

    // Analyze bundle sizes and dependencies
    const modules = (window as any).__webpack_require__?.cache || {};
    const bundleInfo = Object.keys(modules).map(key => {
      const module = modules[key];
      return {
        id: key,
        size: JSON.stringify(module).length,
        exports: Object.keys(module.exports || {})
      };
    });

    console.group('Bundle Analysis');
    console.table(bundleInfo.sort((a, b) => b.size - a.size).slice(0, 10));
    console.groupEnd();
  }

  static trackLargeComponents() {
    if (process.env.NODE_ENV !== 'development') return;

    // Track component render times
    const originalCreateElement = React.createElement;
    
    (React as any).createElement = function(...args: any[]) {
      const start = performance.now();
      const result = originalCreateElement.apply(this, args);
      const end = performance.now();
      
      if (end - start > 16) { // More than one frame
        console.warn(`Slow component render: ${args[0]?.name || args[0]} took ${(end - start).toFixed(2)}ms`);
      }
      
      return result;
    };
  }
}

// Global performance monitor instance
export const performanceMonitor = new PerformanceMonitor();

// Auto-initialize optimizations
if (typeof window !== 'undefined') {
  // Wait for DOM to be ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      ResourceOptimizer.preloadCriticalResources();
      ResourceOptimizer.optimizeImages();
      ResourceOptimizer.implementCriticalCSS();
    });
  } else {
    ResourceOptimizer.preloadCriticalResources();
    ResourceOptimizer.optimizeImages();
    ResourceOptimizer.implementCriticalCSS();
  }

  // Clean up on page unload
  window.addEventListener('beforeunload', () => {
    performanceMonitor.destroy();
  });
}