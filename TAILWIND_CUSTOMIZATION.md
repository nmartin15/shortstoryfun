# Tailwind CSS Customization Guide

## Overview

This document explains how to customize Tailwind CSS for the Short Story Pipeline application.

## Configuration Location

The Tailwind configuration is defined in `templates/index.html` within a `<script>` tag:

```javascript
tailwind.config = {
    darkMode: 'class',
    theme: {
        extend: {
            colors: { /* ... */ },
            fontFamily: { /* ... */ }
        }
    }
}
```

## Current Customizations

### Color Palette

#### Primary Colors (Gold/Yellow Theme)
- `primary`: `#FFD700` - Main gold color
- `primary.dark`: `#CCAA00` - Darker gold for hover states
- `primary.light`: `#FFEE00` - Lighter gold for highlights

**Usage:**
```html
<div class="bg-primary text-black">Primary background</div>
<button class="bg-primary-dark hover:bg-primary">Button</button>
```

#### Background Colors (Dark Theme)
- `background`: `#000000` - Main black background
- `background.secondary`: `#0a0a0a` - Slightly lighter for cards/sections
- `background.tertiary`: `#141414` - Even lighter for nested elements

**Usage:**
```html
<div class="bg-background">Main background</div>
<div class="bg-background-secondary">Card background</div>
<div class="bg-background-tertiary">Nested element</div>
```

### Typography

#### Font Family
- **Primary**: `Inter` (from Google Fonts)
- **Fallback**: `system-ui, sans-serif`

**Usage:**
```html
<p class="font-sans">Text using Inter font</p>
```

## Modifying the Configuration

### Adding New Colors

1. Edit `templates/index.html`
2. Add to the `colors` object in `theme.extend`:

```javascript
tailwind.config = {
    darkMode: 'class',
    theme: {
        extend: {
            colors: {
                primary: {
                    DEFAULT: '#FFD700',
                    dark: '#CCAA00',
                    light: '#FFEE00',
                },
                // Add new color
                accent: {
                    DEFAULT: '#00FF00',
                    dark: '#00CC00',
                },
                background: {
                    DEFAULT: '#000000',
                    secondary: '#0a0a0a',
                    tertiary: '#141414',
                }
            }
        }
    }
}
```

3. Use in HTML:
```html
<div class="bg-accent text-white">Accent color</div>
```

### Adding New Fonts

1. Add font import to HTML `<head>`:
```html
<link href="https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap" rel="stylesheet">
```

2. Update Tailwind config:
```javascript
fontFamily: {
    sans: ['Inter', 'system-ui', 'sans-serif'],
    mono: ['Roboto Mono', 'monospace'], // New font
}
```

3. Use in HTML:
```html
<code class="font-mono">Monospace text</code>
```

### Adding Custom Utilities

To add custom utilities (spacing, shadows, etc.), extend the theme:

```javascript
theme: {
    extend: {
        spacing: {
            '128': '32rem', // Custom spacing
        },
        boxShadow: {
            'gold': '0 4px 6px rgba(255, 215, 0, 0.3)', // Custom shadow
        }
    }
}
```

## Development vs Production

### Development (Current Setup)
- Uses CDN: `https://cdn.tailwindcss.com`
- Configuration in HTML
- Fast iteration, no build step

### Production (Recommended)
1. **Install Tailwind CLI**:
   ```bash
   npm install -D tailwindcss
   npx tailwindcss init
   ```

2. **Create `tailwind.config.js`**:
   ```javascript
   module.exports = {
       content: [
           "./templates/**/*.html",
           "./static/js/**/*.js"
       ],
       darkMode: 'class',
       theme: {
           extend: {
               colors: {
                   primary: {
                       DEFAULT: '#FFD700',
                       dark: '#CCAA00',
                       light: '#FFEE00',
                   },
                   background: {
                       DEFAULT: '#000000',
                       secondary: '#0a0a0a',
                       tertiary: '#141414',
                   }
               },
               fontFamily: {
                   sans: ['Inter', 'system-ui', 'sans-serif'],
               }
           }
       }
   }
   ```

3. **Create input CSS** (`src/input.css`):
   ```css
   @tailwind base;
   @tailwind components;
   @tailwind utilities;
   ```

4. **Build CSS**:
   ```bash
   npx tailwindcss -i ./src/input.css -o ./static/css/tailwind-compiled.css --minify
   ```

5. **Update HTML** to use compiled CSS:
   ```html
   <link rel="stylesheet" href="{{ url_for('static', filename='css/tailwind-compiled.css') }}">
   ```

## Dark Mode

The application uses class-based dark mode:

```javascript
darkMode: 'class'
```

This means dark mode is activated by adding the `dark` class to the `<html>` element:

```html
<html class="dark">
```

Or toggle dynamically:
```javascript
document.documentElement.classList.toggle('dark');
```

## Best Practices

1. **Use theme colors**: Always use theme colors instead of hardcoded hex values
   - ✅ `bg-primary`
   - ❌ `bg-[#FFD700]`

2. **Extend, don't override**: Use `theme.extend` to add customizations without losing defaults

3. **Responsive design**: Use Tailwind's responsive prefixes:
   ```html
   <div class="text-sm md:text-base lg:text-lg">Responsive text</div>
   ```

4. **Dark mode variants**: Consider dark mode when adding styles:
   ```html
   <div class="bg-white dark:bg-background-secondary">Adaptive background</div>
   ```

## Common Customizations

### Adding a Custom Button Style

Create a component class in your CSS or use Tailwind's `@apply`:

```css
.btn-primary {
    @apply bg-primary text-black font-semibold py-2 px-4 rounded hover:bg-primary-dark;
}
```

### Custom Animations

Add to Tailwind config:

```javascript
theme: {
    extend: {
        animation: {
            'fade-in': 'fadeIn 0.5s ease-in',
        },
        keyframes: {
            fadeIn: {
                '0%': { opacity: '0' },
                '100%': { opacity: '1' },
            }
        }
    }
}
```

## Troubleshooting

### Styles Not Applying
1. Check that Tailwind CDN is loaded
2. Verify class names are correct
3. Check for CSS specificity issues
4. Clear browser cache

### Dark Mode Not Working
1. Ensure `darkMode: 'class'` is set
2. Verify `dark` class is on `<html>` element
3. Check that dark mode variants are used: `dark:bg-...`

### Custom Colors Not Available
1. Verify colors are in `theme.extend.colors`
2. Restart development server if using build process
3. Check for typos in color names

## References

- [Tailwind CSS Documentation](https://tailwindcss.com/docs)
- [Tailwind Configuration](https://tailwindcss.com/docs/configuration)
- [Dark Mode](https://tailwindcss.com/docs/dark-mode)
- [Theme Customization](https://tailwindcss.com/docs/theme)

