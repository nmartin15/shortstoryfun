/**
 * Jest setup file for JavaScript tests.
 * Configures testing environment and global mocks.
 */

// Setup fetch mock
require('jest-fetch-mock').enableMocks();

// Mock window.URL for blob URL creation
global.URL = {
    createObjectURL: jest.fn(() => 'blob:mock-url'),
    revokeObjectURL: jest.fn()
};

// Reset mocks before each test
beforeEach(() => {
    fetch.resetMocks();
    global.URL.createObjectURL.mockClear();
    global.URL.revokeObjectURL.mockClear();
});

