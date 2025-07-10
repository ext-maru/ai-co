/**
 * Accessibility utilities and WCAG 2.2 compliance
 */

export interface AccessibilityOptions {
  enableKeyboardNavigation?: boolean;
  enableScreenReaderSupport?: boolean;
  enableHighContrast?: boolean;
  enableReducedMotion?: boolean;
  enableFocusManagement?: boolean;
}

export class AccessibilityManager {
  private options: AccessibilityOptions;
  private focusableElements: string = [
    'a[href]',
    'button:not([disabled])',
    'textarea:not([disabled])',
    'input[type="text"]:not([disabled])',
    'input[type="radio"]:not([disabled])',
    'input[type="checkbox"]:not([disabled])',
    'select:not([disabled])',
    '[tabindex]:not([tabindex="-1"])'
  ].join(', ');

  private trapStack: HTMLElement[] = [];

  constructor(options: AccessibilityOptions = {}) {
    this.options = {
      enableKeyboardNavigation: true,
      enableScreenReaderSupport: true,
      enableHighContrast: false,
      enableReducedMotion: false,
      enableFocusManagement: true,
      ...options
    };

    this.initialize();
  }

  private initialize() {
    if (typeof window === 'undefined') return;

    this.setupKeyboardNavigation();
    this.setupScreenReaderSupport();
    this.setupMotionPreferences();
    this.setupHighContrastMode();
    this.setupFocusManagement();
    this.announcePageLoad();
  }

  private setupKeyboardNavigation() {
    if (!this.options.enableKeyboardNavigation) return;

    document.addEventListener('keydown', (event) => {
      // Skip to main content with Alt+S
      if (event.altKey && event.key === 's') {
        event.preventDefault();
        const main = document.querySelector('main') as HTMLElement;
        if (main) {
          main.focus();
          this.announceToScreenReader('Skipped to main content');
        }
      }

      // Skip to navigation with Alt+N
      if (event.altKey && event.key === 'n') {
        event.preventDefault();
        const nav = document.querySelector('nav') as HTMLElement;
        if (nav) {
          const firstFocusable = nav.querySelector(this.focusableElements) as HTMLElement;
          if (firstFocusable) {
            firstFocusable.focus();
            this.announceToScreenReader('Skipped to navigation');
          }
        }
      }

      // Escape key handling
      if (event.key === 'Escape') {
        this.handleEscapeKey();
      }

      // Tab trap handling
      if (event.key === 'Tab') {
        this.handleTabTrap(event);
      }
    });

    // Add skip links
    this.addSkipLinks();
  }

  private addSkipLinks() {
    const skipLinks = document.createElement('div');
    skipLinks.className = 'skip-links';
    skipLinks.innerHTML = `
      <a href="#main" class="skip-link">Skip to main content</a>
      <a href="#nav" class="skip-link">Skip to navigation</a>
    `;

    // Add CSS for skip links
    const style = document.createElement('style');
    style.textContent = `
      .skip-links {
        position: fixed;
        top: -100px;
        left: 0;
        z-index: 9999;
      }

      .skip-link {
        position: absolute;
        top: 0;
        left: 0;
        background: #000;
        color: #fff;
        padding: 8px 16px;
        text-decoration: none;
        border-radius: 0 0 4px 0;
        transition: top 0.3s;
      }

      .skip-link:focus {
        top: 0;
      }
    `;

    document.head.appendChild(style);
    document.body.insertBefore(skipLinks, document.body.firstChild);
  }

  private setupScreenReaderSupport() {
    if (!this.options.enableScreenReaderSupport) return;

    // Create live region for announcements
    const liveRegion = document.createElement('div');
    liveRegion.id = 'aria-live-region';
    liveRegion.setAttribute('aria-live', 'polite');
    liveRegion.setAttribute('aria-atomic', 'true');
    liveRegion.style.position = 'absolute';
    liveRegion.style.left = '-10000px';
    liveRegion.style.width = '1px';
    liveRegion.style.height = '1px';
    liveRegion.style.overflow = 'hidden';

    document.body.appendChild(liveRegion);

    // Create assertive live region for urgent announcements
    const assertiveRegion = document.createElement('div');
    assertiveRegion.id = 'aria-live-assertive';
    assertiveRegion.setAttribute('aria-live', 'assertive');
    assertiveRegion.setAttribute('aria-atomic', 'true');
    assertiveRegion.style.position = 'absolute';
    assertiveRegion.style.left = '-10000px';
    assertiveRegion.style.width = '1px';
    assertiveRegion.style.height = '1px';
    assertiveRegion.style.overflow = 'hidden';

    document.body.appendChild(assertiveRegion);
  }

  private setupMotionPreferences() {
    if (typeof window === 'undefined') return;

    // Detect user motion preferences
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    if (prefersReducedMotion || this.options.enableReducedMotion) {
      document.documentElement.classList.add('reduce-motion');

      // Add CSS for reduced motion
      const style = document.createElement('style');
      style.textContent = `
        .reduce-motion *,
        .reduce-motion *::before,
        .reduce-motion *::after {
          animation-duration: 0.01ms !important;
          animation-iteration-count: 1 !important;
          transition-duration: 0.01ms !important;
          scroll-behavior: auto !important;
        }
      `;
      document.head.appendChild(style);
    }
  }

  private setupHighContrastMode() {
    const prefersHighContrast = window.matchMedia('(prefers-contrast: high)').matches;

    if (prefersHighContrast || this.options.enableHighContrast) {
      document.documentElement.classList.add('high-contrast');

      // Add high contrast CSS
      const style = document.createElement('style');
      style.textContent = `
        .high-contrast {
          --primary-color: #000000;
          --secondary-color: #ffffff;
          --accent-color: #0066cc;
          --error-color: #cc0000;
          --success-color: #006600;
          --warning-color: #cc6600;
        }

        .high-contrast * {
          border-color: currentColor !important;
        }

        .high-contrast button,
        .high-contrast input,
        .high-contrast select,
        .high-contrast textarea {
          border: 2px solid currentColor !important;
        }

        .high-contrast a {
          text-decoration: underline !important;
        }

        .high-contrast :focus {
          outline: 3px solid #0066cc !important;
          outline-offset: 2px !important;
        }
      `;
      document.head.appendChild(style);
    }
  }

  private setupFocusManagement() {
    if (!this.options.enableFocusManagement) return;

    // Enhance focus visibility
    const style = document.createElement('style');
    style.textContent = `
      :focus-visible {
        outline: 3px solid #005fcc;
        outline-offset: 2px;
        border-radius: 2px;
      }

      button:focus-visible,
      input:focus-visible,
      select:focus-visible,
      textarea:focus-visible,
      [tabindex]:focus-visible {
        box-shadow: 0 0 0 3px rgba(0, 95, 204, 0.3);
      }
    `;
    document.head.appendChild(style);

    // Track focus for debugging
    if (process.env.NODE_ENV === 'development') {
      document.addEventListener('focus', (event) => {
        console.log('Focus moved to:', event.target);
      }, true);
    }
  }

  private announcePageLoad() {
    // Announce page title to screen readers
    setTimeout(() => {
      const title = document.title;
      this.announceToScreenReader(`Page loaded: ${title}`);
    }, 1000);
  }

  private handleEscapeKey() {
    // Close modals, dropdowns, etc.
    const openModal = document.querySelector('[role="dialog"][aria-hidden="false"]') as HTMLElement;
    if (openModal) {
      this.closeModal(openModal);
      return;
    }

    // Close expanded dropdowns
    const expandedDropdown = document.querySelector('[aria-expanded="true"]') as HTMLElement;
    if (expandedDropdown) {
      expandedDropdown.setAttribute('aria-expanded', 'false');
      expandedDropdown.focus();
    }
  }

  private handleTabTrap(event: KeyboardEvent) {
    if (this.trapStack.length === 0) return;

    const trap = this.trapStack[this.trapStack.length - 1];
    const focusableElements = Array.from(trap.querySelectorAll(this.focusableElements)) as HTMLElement[];

    if (focusableElements.length === 0) return;

    const firstFocusable = focusableElements[0];
    const lastFocusable = focusableElements[focusableElements.length - 1];

    if (event.shiftKey) {
      // Shift + Tab
      if (document.activeElement === firstFocusable) {
        event.preventDefault();
        lastFocusable.focus();
      }
    } else {
      // Tab
      if (document.activeElement === lastFocusable) {
        event.preventDefault();
        firstFocusable.focus();
      }
    }
  }

  public announceToScreenReader(message: string, priority: 'polite' | 'assertive' = 'polite') {
    const regionId = priority === 'assertive' ? 'aria-live-assertive' : 'aria-live-region';
    const region = document.getElementById(regionId);

    if (region) {
      // Clear previous message
      region.textContent = '';

      // Add new message after a brief delay
      setTimeout(() => {
        region.textContent = message;
      }, 100);

      // Clear message after it's been announced
      setTimeout(() => {
        region.textContent = '';
      }, 3000);
    }
  }

  public trapFocus(element: HTMLElement) {
    this.trapStack.push(element);

    // Focus first focusable element
    const focusableElements = element.querySelectorAll(this.focusableElements);
    if (focusableElements.length > 0) {
      (focusableElements[0] as HTMLElement).focus();
    }
  }

  public releaseFocusTrap() {
    this.trapStack.pop();
  }

  public openModal(modal: HTMLElement, triggerElement?: HTMLElement) {
    // Set modal attributes
    modal.setAttribute('role', 'dialog');
    modal.setAttribute('aria-modal', 'true');
    modal.setAttribute('aria-hidden', 'false');

    // Store trigger element for later focus restoration
    if (triggerElement) {
      modal.dataset.triggerElement = triggerElement.id || this.generateId();
      if (!triggerElement.id) {
        triggerElement.id = modal.dataset.triggerElement;
      }
    }

    // Trap focus in modal
    this.trapFocus(modal);

    // Announce modal opening
    const modalTitle = modal.querySelector('h1, h2, h3, [role="heading"]')?.textContent || 'Modal dialog';
    this.announceToScreenReader(`${modalTitle} dialog opened`, 'assertive');
  }

  public closeModal(modal: HTMLElement) {
    // Set modal attributes
    modal.setAttribute('aria-hidden', 'true');

    // Release focus trap
    this.releaseFocusTrap();

    // Restore focus to trigger element
    const triggerElementId = modal.dataset.triggerElement;
    if (triggerElementId) {
      const triggerElement = document.getElementById(triggerElementId) as HTMLElement;
      if (triggerElement) {
        triggerElement.focus();
      }
    }

    // Announce modal closing
    this.announceToScreenReader('Dialog closed', 'assertive');
  }

  public setPageTitle(title: string) {
    document.title = title;
    this.announceToScreenReader(`Page title changed to: ${title}`);
  }

  public announceError(message: string) {
    this.announceToScreenReader(`Error: ${message}`, 'assertive');
  }

  public announceSuccess(message: string) {
    this.announceToScreenReader(`Success: ${message}`, 'polite');
  }

  public announceLoading(isLoading: boolean, context?: string) {
    if (isLoading) {
      const message = context ? `Loading ${context}` : 'Loading';
      this.announceToScreenReader(message, 'polite');
    } else {
      const message = context ? `${context} loaded` : 'Loading complete';
      this.announceToScreenReader(message, 'polite');
    }
  }

  private generateId(): string {
    return `a11y-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }

  private closeModal(modal: HTMLElement) {
    modal.setAttribute('aria-hidden', 'true');
    this.releaseFocusTrap();

    const triggerElementId = modal.dataset.triggerElement;
    if (triggerElementId) {
      const triggerElement = document.getElementById(triggerElementId) as HTMLElement;
      if (triggerElement) {
        triggerElement.focus();
      }
    }
  }

  public validateForm(form: HTMLFormElement): { isValid: boolean; errors: string[] } {
    const errors: string[] = [];
    const requiredFields = form.querySelectorAll('[required]') as NodeListOf<HTMLInputElement>;

    requiredFields.forEach(field => {
      if (!field.value.trim()) {
        const label = form.querySelector(`label[for="${field.id}"]`)?.textContent || field.name || 'Field';
        errors.push(`${label} is required`);

        // Add aria-invalid attribute
        field.setAttribute('aria-invalid', 'true');

        // Add or update error message
        this.setFieldError(field, `${label} is required`);
      } else {
        field.removeAttribute('aria-invalid');
        this.clearFieldError(field);
      }
    });

    // Announce validation results
    if (errors.length > 0) {
      this.announceError(`Form has ${errors.length} error${errors.length > 1 ? 's' : ''}`);
    }

    return {
      isValid: errors.length === 0,
      errors
    };
  }

  private setFieldError(field: HTMLInputElement, message: string) {
    let errorElement = document.getElementById(`${field.id}-error`);

    if (!errorElement) {
      errorElement = document.createElement('div');
      errorElement.id = `${field.id}-error`;
      errorElement.className = 'field-error';
      errorElement.setAttribute('role', 'alert');
      field.parentNode?.insertBefore(errorElement, field.nextSibling);

      // Link error to field
      field.setAttribute('aria-describedby', errorElement.id);
    }

    errorElement.textContent = message;
  }

  private clearFieldError(field: HTMLInputElement) {
    const errorElement = document.getElementById(`${field.id}-error`);
    if (errorElement) {
      errorElement.remove();
      field.removeAttribute('aria-describedby');
    }
  }
}

// Color contrast utilities
export class ColorContrastChecker {
  static getContrastRatio(color1: string, color2: string): number {
    const luminance1 = this.getLuminance(color1);
    const luminance2 = this.getLuminance(color2);

    const lighter = Math.max(luminance1, luminance2);
    const darker = Math.min(luminance1, luminance2);

    return (lighter + 0.05) / (darker + 0.05);
  }

  static meetsWCAGAA(color1: string, color2: string): boolean {
    return this.getContrastRatio(color1, color2) >= 4.5;
  }

  static meetsWCAGAAA(color1: string, color2: string): boolean {
    return this.getContrastRatio(color1, color2) >= 7;
  }

  private static getLuminance(color: string): number {
    const rgb = this.hexToRgb(color);
    if (!rgb) return 0;

    const { r, g, b } = rgb;

    const rsRGB = r / 255;
    const gsRGB = g / 255;
    const bsRGB = b / 255;

    const r2 = rsRGB <= 0.03928 ? rsRGB / 12.92 : Math.pow((rsRGB + 0.055) / 1.055, 2.4);
    const g2 = gsRGB <= 0.03928 ? gsRGB / 12.92 : Math.pow((gsRGB + 0.055) / 1.055, 2.4);
    const b2 = bsRGB <= 0.03928 ? bsRGB / 12.92 : Math.pow((bsRGB + 0.055) / 1.055, 2.4);

    return 0.2126 * r2 + 0.7152 * g2 + 0.0722 * b2;
  }

  private static hexToRgb(hex: string): { r: number; g: number; b: number } | null {
    const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    return result ? {
      r: parseInt(result[1], 16),
      g: parseInt(result[2], 16),
      b: parseInt(result[3], 16)
    } : null;
  }
}

// Global accessibility manager
export const accessibilityManager = new AccessibilityManager();

// Auto-initialize accessibility features
if (typeof window !== 'undefined') {
  // Check for user preferences
  const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const prefersHighContrast = window.matchMedia('(prefers-contrast: high)').matches;

  if (prefersReducedMotion || prefersHighContrast) {
    // Reinitialize with user preferences
    const options: AccessibilityOptions = {
      enableReducedMotion: prefersReducedMotion,
      enableHighContrast: prefersHighContrast
    };

    // Note: In a real implementation, you might want to update the existing instance
    // rather than creating a new one
  }
}
