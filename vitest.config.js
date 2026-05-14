import { defineConfig } from 'vitest/config'

export default defineConfig({
  test: {
    environment: 'jsdom',
    environmentOptions: {
      jsdom: {
        runScripts: 'dangerously'
      }
    },
    include: ['tests/js/**/*.test.js'],
    globals: false,
    restoreMocks: true,
    clearMocks: true
  }
})
