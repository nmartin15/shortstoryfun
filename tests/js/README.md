# JavaScript Test Suite

This directory contains comprehensive tests for the frontend JavaScript code in `static/js/app.js`.

## Setup

Tests use Jest with jsdom for DOM testing. Dependencies are installed via npm:

```bash
npm install
```

## Running Tests

### Run all JavaScript tests
```bash
npm test
```

### Run tests in watch mode
```bash
npm run test:watch
```

### Run tests with coverage
```bash
npm run test:coverage
```

## Test Coverage

The test suite covers:

1. **XSS Prevention**
   - HTML escaping (`escapeHtml`)
   - Script tag prevention
   - Event handler prevention
   - JavaScript protocol prevention

2. **API Error Handling**
   - JSON error responses
   - Non-JSON error responses
   - Default error handling

3. **Word Counting**
   - Basic word counting
   - Handling of whitespace
   - Edge cases (null, undefined, empty strings)

4. **UI State Management**
   - Error display/hiding
   - Loading indicators
   - Success messages

5. **Form Validation**
   - Required field validation
   - Genre selection validation

6. **API Integration**
   - Story generation
   - Story loading
   - Story saving
   - Export functionality
   - Template loading
   - Revision history

7. **Story Browser**
   - Story list loading
   - Individual story loading
   - Pagination

## Test Structure

- `setup.js` - Jest configuration and global mocks
- `app.test.js` - Main test suite for app.js functions

## Notes

- Tests use jsdom to simulate the browser DOM
- External libraries (lucide, gsap) are mocked
- Fetch API is mocked using jest-fetch-mock
- Tests are isolated and can run independently

