import { afterEach, describe, expect, it } from 'vitest'

import {
  clearAccessToken,
  getAccessToken,
  setAccessToken,
} from '@/features/auth/session'

describe('auth session store', () => {
  afterEach(() => {
    clearAccessToken()
  })

  it('starts with no access token', () => {
    expect(getAccessToken()).toBeNull()
  })

  it('stores and clears the access token', () => {
    setAccessToken('jwt.access.token')
    expect(getAccessToken()).toBe('jwt.access.token')
    clearAccessToken()
    expect(getAccessToken()).toBeNull()
  })

  it('ignores duplicate set of the same token', () => {
    setAccessToken('same')
    setAccessToken('same')
    expect(getAccessToken()).toBe('same')
  })
})
